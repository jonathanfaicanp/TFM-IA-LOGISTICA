import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_conversational_sql_correction import (
    audit, compatible, compare_case, equal, match_case, validate_cases, validate_paths,
)
from evaluation.conversational_dataset import build_artifact, GROUP_ORDER
from src.analytical_service import AnalyticalService


def results():
    rows = []
    for group in range(4):
        for index in range(5):
            status, coverage = (('NO_RELEVANT_DEVIATION', 'COMPLETE'),
                                ('REVIEW', 'COMPLETE'), ('NOT_EVALUABLE', 'NONE'),
                                ('NO_RELEVANT_DEVIATION', 'PARTIAL'))[group]
            consumption_status = status if group != 3 else 'NOT_EVALUABLE'
            common = {'distancia_km': 2 + (group * 5 + index) / 100,
                      'reason': 'fixture', 'status': consumption_status,
                      'relative_deviation': .75, 'robust_z': 3.0,
                      'baseline': 10.0, 'mad': 2.0, 'historical_observations': 100}
            rows.append({'trip_id': f'trip-{group}-{index}', 'vehicle_id': 'private',
                         'timestamp': '2026-01-01', 'distance_km': common['distancia_km'],
                         'overall_status': status, 'analysis_coverage': coverage,
                         'review_signals': ['consumption', 'temporal'] if group == 1 else [],
                         'signals': {'consumption': {**common, 'consumo_litros': .5, 'consumo_l_100km': 17.5},
                                     'temporal': {**common, 'status': status,
                                                  'minutes_per_km': 3.0, 'duration_minutes': 6.0}}})
    return rows


def original(rows):
    document = build_artifact(rows)
    for case in document['cases']:
        for key in ('baseline', 'mad', 'consumo_litros', 'consumo_l_100km'):
            case['signals']['consumption'][key] *= 1000
    return document


class AuditCorrectionTests(unittest.TestCase):
    def test_unique_multiple_and_no_match(self):
        rows = results(); case = original(rows)['cases'][0]
        self.assertEqual(match_case(case, rows)[0], 'UNIQUE_MATCH')
        match = match_case(case, rows)[1][0]
        other = copy.deepcopy(match); other['trip_id'] = 'different'
        self.assertEqual(match_case(case, [match, other])[0], 'MULTIPLE_MATCHES')
        other['signals']['temporal']['minutes_per_km'] += 1
        self.assertEqual(match_case(case, [other])[0], 'NO_MATCH')

    def test_explicit_float_tolerance_and_null(self):
        self.assertTrue(equal(1.0, 1.0 + 1e-10))
        self.assertFalse(equal(1.0, 1.0 + 1e-5))
        self.assertTrue(equal(None, None))
        self.assertFalse(equal(None, 0))
        self.assertFalse(equal(True, 1))
        self.assertFalse(equal(float('nan'), float('nan')))

    def test_consumption_absolute_values_do_not_resolve_ambiguity(self):
        rows = results(); case = original(rows)['cases'][0]
        match = match_case(case, rows)[1][0]
        other = copy.deepcopy(match); other['trip_id'] = 'different'
        other['signals']['consumption']['baseline'] = 999999
        self.assertTrue(compatible(case, other))
        self.assertEqual(match_case(case, [match, other])[0], 'MULTIPLE_MATCHES')

    def test_factor_observed_and_not_assumed(self):
        rows = results(); case = original(rows)['cases'][0]
        corrected = build_artifact(rows)['cases'][0]
        comparisons = compare_case(case, corrected)
        self.assertEqual(sum(r['factor_1000'] for r in comparisons), 4)
        corrected['signals']['consumption']['mad'] = 7
        mad = next(r for r in compare_case(case, corrected) if r['field'] == 'signals.consumption.mad')
        self.assertFalse(mad['factor_1000'])
        case['signals']['consumption']['mad'] = 0
        corrected['signals']['consumption']['mad'] = 0
        mad = next(r for r in compare_case(case, corrected) if r['field'] == 'signals.consumption.mad')
        self.assertIsNone(mad['ratio_original_to_corrected'])

    def test_original_validation(self):
        document = original(results()); validate_cases(document)
        document['cases'][0]['case_id'] = document['cases'][1]['case_id']
        with self.assertRaises(ValueError): validate_cases(document)

    def run_fixture(self, folder, rows):
        data = Path(folder) / 'data'; source = data / 'original/cases.json'
        source.parent.mkdir(parents=True)
        source.write_text(json.dumps(original(results())), encoding='utf-8')
        before = source.read_bytes()
        repo = Mock(); repo.load_historical_rows.return_value = []
        repo.load_rows_between.return_value = rows
        service = Mock(); service.evaluate.side_effect = lambda row: SimpleNamespace(to_dict=lambda: copy.deepcopy(row))
        output = data / 'audit'
        with patch('audit_conversational_sql_correction.AnalyticalService.from_history', return_value=service):
            summary = audit(source, output, repo, data_root=data)
        self.assertEqual(before, source.read_bytes())
        self.assertEqual(repo.load_rows_between.call_args.args[0].year, 2026)
        self.assertEqual(repo.load_rows_between.call_args.args[1].year, 2027)
        return summary, source, output, data

    def test_full_audit_preserves_originals_and_anonymizes_corrected(self):
        with tempfile.TemporaryDirectory() as folder:
            summary, source, output, data = self.run_fixture(folder, results())
            self.assertEqual(summary['matching']['UNIQUE_MATCH'], 20)
            corrected = json.loads((output / 'corrected_cases.json').read_text())
            self.assertEqual([c['case_id'] for c in corrected['cases']], [c['case_id'] for c in original(results())['cases']])
            self.assertFalse(any('trip_id' in c for c in corrected['cases']))
            self.assertTrue((output / 'case_mapping_private.json').exists())
            self.assertEqual(summary['scale_affected_cases'], 20)
            with self.assertRaises(ValueError): validate_paths(source, output, data)
            with self.assertRaises(ValueError): validate_paths(source, source.parent, data)
            with self.assertRaises(ValueError): validate_paths(source, Path(folder) / 'outside', data)

    def test_ambiguous_matches_never_generate_corrected_cases(self):
        rows = results(); extra = copy.deepcopy(rows[0]); extra['trip_id'] = 'other'; rows.append(extra)
        with tempfile.TemporaryDirectory() as folder:
            summary, _, output, _ = self.run_fixture(folder, rows)
            self.assertEqual(summary['matching']['MULTIPLE_MATCHES'], 1)
            self.assertFalse((output / 'corrected_cases.json').exists())

    def test_missing_match_never_generates_corrected_cases(self):
        with tempfile.TemporaryDirectory() as folder:
            summary, _, output, _ = self.run_fixture(folder, results()[1:])
            self.assertEqual(summary['matching']['NO_MATCH'], 1)
            self.assertFalse((output / 'corrected_cases.json').exists())

    def test_real_engine_with_fake_sql_and_historically_scaled_artifact(self):
        history = [{'Codigo Viaje': f'h-{i}', 'Codigo Vehiculo': 'v',
                    'Fecha de inicio': '2024-01-01', 'Distancia': 10000,
                    'Consumo': 1000 + 10 * i, 'Duracion': 120 + i}
                   for i in range(100)]
        candidates = []
        for group in range(4):
            for i in range(5):
                candidates.append({'Codigo Viaje': f'e-{group}-{i}',
                                   'Codigo Vehiculo': 'unknown' if group == 2 else 'v',
                                   'Fecha de inicio': '2026-01-01',
                                   'Distancia': 10000 + (group * 5 + i) * 100,
                                   'Consumo': (1495, 10000, 0, 0)[group],
                                   'Duracion': (170, 1200, 0, 170)[group]})
        def old_scale(row):
            return {**row, 'Consumo': row['Consumo'] * 1000}
        old_service = AnalyticalService.from_history(map(old_scale, history))
        document = build_artifact(old_service.evaluate(old_scale(row)).to_dict() for row in candidates)
        validate_cases(document)
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder) / 'data'; source = data / 'original/cases.json'
            source.parent.mkdir(parents=True)
            source.write_text(json.dumps(document), encoding='utf-8')
            repo = Mock(); repo.load_historical_rows.return_value = history
            repo.load_rows_between.return_value = candidates
            summary = audit(source, data / 'audit', repo, data_root=data)
            self.assertEqual(summary['matching']['UNIQUE_MATCH'], 20)
            self.assertEqual(summary['scale_affected_cases'], 10)
            self.assertEqual(summary['state_changed_cases'], 0)
            self.assertEqual(summary['relative_deviation_changed_cases'], 0)
            self.assertEqual(summary['robust_z_changed_cases'], 0)
            self.assertTrue(summary['corrected_cases_generated'])
