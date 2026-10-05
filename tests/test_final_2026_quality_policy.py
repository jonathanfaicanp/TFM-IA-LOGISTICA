"""Invented fixtures only; no private snapshot counts embedded in the policy."""
import copy
from datetime import date
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from evaluate_final_2026_quality_policy import evaluate_rows, apply_quality_policy
from src.analytical_service import AnalyticalService
from src.models import DetectionStatus


def row(identifier, timestamp='2026-08-20 00:00:00', consumption=4000, duration=360):
    return {'Codigo Viaje': identifier, 'Codigo Vehiculo': 'SYNTHETIC_VEHICLE_001',
            'Fecha de inicio': timestamp, 'Distancia': 2000, 'Consumo': consumption, 'Duracion': duration}


def history():
    return [row(f'SYNTHETIC_HISTORY_{i}', f'{2024+i//50}-01-01',
                (800,900,1000,1100,1200)[i%5], (240,300,360,420,480)[i%5]) for i in range(100)]


class QualityPolicyTests(unittest.TestCase):
    def test_boundary_and_source_magnitudes_unchanged(self):
        service = AnalyticalService.from_history(history())
        for timestamp, excluded in [('2026-08-19 23:59:59', False), ('2026-08-20 00:00:00', True)]:
            original = service.consumption_detector.evaluate(row('SYNTHETIC_TRIP', timestamp))
            result = apply_quality_policy(original)
            self.assertEqual(result.status, DetectionStatus.NOT_EVALUABLE if excluded else original.status)
            self.assertEqual(original.consumo_litros, 4)
            self.assertEqual(result.consumo_litros, 4)
            self.assertEqual(result.consumo_l_100km, original.consumo_l_100km)
            self.assertEqual(original.status, DetectionStatus.REVIEW)

    def test_complete_to_partial_and_no_relevant_consolidation(self):
        result = evaluate_rows(history()+[row('SYNTHETIC_TRIP')])
        self.assertEqual(result['consolidation_before_policy']['overall_status']['REVIEW'], 1)
        self.assertEqual(result['consolidation_final']['overall_status']['NO_RELEVANT_DEVIATION'], 1)
        self.assertEqual(result['consolidation_before_policy']['analysis_coverage']['COMPLETE'], 1)
        self.assertEqual(result['consolidation_final']['analysis_coverage']['PARTIAL'], 1)
        self.assertTrue(result['delta']['all_affected_evaluable_were_review'])

    def test_temporal_review_survives(self):
        result = evaluate_rows(history()+[row('SYNTHETIC_TRIP', duration=1200)])
        self.assertTrue(result['temporal_preserved'])
        self.assertEqual(result['consolidation_final']['review_signals']['only_temporal'], 1)
        self.assertEqual(result['consolidation_final']['overall_status']['REVIEW'], 1)

    def test_partial_to_none(self):
        result = evaluate_rows(history()+[row('SYNTHETIC_TRIP', duration=0)])
        self.assertEqual(result['consolidation_before_policy']['analysis_coverage']['PARTIAL'], 1)
        self.assertEqual(result['consolidation_final']['analysis_coverage']['NONE'], 1)
        self.assertEqual(result['consolidation_final']['overall_status']['NOT_EVALUABLE'], 1)

    def test_non_review_affected_is_reported_not_assumed(self):
        result = evaluate_rows(history()+[row('SYNTHETIC_TRIP', consumption=1000)])
        self.assertFalse(result['delta']['all_affected_evaluable_were_review'])
        self.assertEqual(result['delta']['affected_review_rate'], 0)

    def test_input_rows_are_not_modified(self):
        rows = history()+[row('SYNTHETIC_TRIP')]
        original = copy.deepcopy(rows)
        evaluate_rows(rows)
        self.assertEqual(rows, original)

    def test_pre_boundary_remains_evaluable_and_empty_delta_undefined(self):
        result = evaluate_rows(history()+[row('SYNTHETIC_TRIP', '2026-08-19')])
        self.assertEqual(result['consumption_final_comparable']['evaluable'], 1)
        self.assertEqual(result['consumption_with_policy_all_2026']['evaluable'], 1)
        self.assertIsNone(result['delta']['affected_review_rate'])


if __name__ == '__main__': unittest.main()
