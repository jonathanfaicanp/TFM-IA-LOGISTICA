import csv
import importlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from experimental_split import validate_split


class ExperimentalSplitTests(unittest.TestCase):
    def test_reject_empty_duplicate_overlap_and_future_history(self):
        for years in ((), (2024, 2024), (2025,), (2026,)):
            with self.subTest(years=years), self.assertRaises(ValueError):
                validate_split(years, 2025)

    def test_all_loaders_exclude_2026_before_feature_conversion(self):
        modules = ('evaluate_detector_candidates', 'analyze_distance_threshold_sensitivity',
                   'analyze_b30_mad', 'analyze_temporal_robustness',
                   'evaluate_synthetic_benchmark', 'evaluate_temporal_synthetic_benchmark')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'input.csv'
            fields = ['Fecha de inicio', 'Codigo Vehiculo', 'Distancia', 'Consumo', 'Duracion']
            with path.open('w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fields, delimiter=';')
                writer.writeheader()
                for year, value in ((2024, '2000'), (2025, '3000'), (2026, 'DO_NOT_PARSE')):
                    writer.writerow(dict(zip(fields, (f'{year}-01-01', str(year), value, value, value))))
            for name in modules:
                with self.subTest(module=name):
                    history, evaluation = importlib.import_module(name).load_records(path, (2024,), 2025)
                    self.assertEqual([r['vehicle'] for r in history], ['2024'])
                    self.assertEqual([r['vehicle'] for r in evaluation], ['2025'])

    def test_default_split_still_uses_2024_2025_for_history(self):
        from evaluate_detector_candidates import load_records
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'input.csv'
            path.write_text('Fecha de inicio;Codigo Vehiculo;Distancia;Consumo\n2024-01-01;A;2000;1000\n2025-01-01;B;2000;1000\n2026-01-01;C;2000;1000\n', encoding='utf-8')
            history, evaluation = load_records(path)
            self.assertEqual([r['vehicle'] for r in history], ['A', 'B'])
            self.assertEqual([r['vehicle'] for r in evaluation], ['C'])

    def test_validation_runner_is_invariant_to_2026_features(self):
        from validate_methodology_2025 import run
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            fields = ['Fecha de inicio', 'Codigo Vehiculo', 'Distancia',
                      'Consumo', 'Duracion', 'Indicador de conduccion']
            results = []
            for variant, future_value in enumerate(('4000', 'DO_NOT_PARSE')):
                path = base / f'input_{variant}.csv'
                with path.open('w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fields, delimiter=';')
                    writer.writeheader()
                    for i in range(100):
                        writer.writerow(dict(zip(fields, ('2024-01-01', '1', '2000',
                                                          str(1000 + i * 10), str(120 + i), '0'))))
                    writer.writerow(dict(zip(fields, ('2025-01-01', '1', '2000', '3000', '240', '0'))))
                    writer.writerow(dict(zip(fields, ('2026-01-01', '1', future_value,
                                                      future_value, future_value, '0'))))
                result = run(path, base / f'output_{variant}')
                result.pop('input_sha256')
                results.append(result)
            self.assertEqual(results[0], results[1])
            self.assertEqual(results[0]['evaluation_year'], 2025)
            self.assertEqual(results[0]['baseline_eligible'][1]['evaluable_records'], 1)
            self.assertFalse(results[0]['final_2026_executed'])
            output = base / 'output_0'
            self.assertTrue((output / 'mad_original/b30_mad_2025_summary.json').exists())
            self.assertFalse(any('2026' in p.name for p in output.rglob('*')))
