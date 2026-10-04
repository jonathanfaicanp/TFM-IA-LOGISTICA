import sys
import csv
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_b30_mad import build_scopes
from evaluate_synthetic_benchmark import (
    RULES,
    apply_rule,
    build_rule_comparison,
    load_records,
    perturb_consumption,
    perturb_record,
    perturbed_l100,
    prepare_evaluation,
    rates,
)


class SyntheticBenchmarkTests(unittest.TestCase):
    def test_consumption_is_perturbed_correctly(self):
        self.assertEqual(perturb_consumption(10.0, .5), 15.0)

    def test_distance_and_source_record_are_not_modified(self):
        source = {"consumption_liters": 10.0, "distance_km": 20.0, "l_100km": 50.0}
        perturbed = perturb_record(source, .5)
        self.assertEqual(perturbed["distance_km"], 20.0)
        self.assertEqual(source, {"consumption_liters": 10.0, "distance_km": 20.0, "l_100km": 50.0})

    def test_l100_is_recalculated_from_unchanged_distance(self):
        self.assertEqual(perturbed_l100(2.0, 10.0, 1.0), 40.0)

    def test_historical_baseline_is_not_contaminated(self):
        history = self._history()
        before = build_scopes(history)
        prepared = prepare_evaluation(history, [self._evaluation_record()])
        perturb_record(prepared[0], 5.0)
        after = build_scopes(history)
        self.assertEqual(before[0]["1"][0], 10.0)
        self.assertEqual(after, before)

    def test_historical_mad_is_not_contaminated(self):
        history = self._history()
        before = build_scopes(history)
        prepared = prepare_evaluation(history, [self._evaluation_record()])
        perturb_record(prepared[0], 5.0)
        after = build_scopes(history)
        self.assertEqual(before[0]["1"][1], 1.0)
        self.assertEqual(after[0]["1"][1:], before[0]["1"][1:])

    def test_vehicle_below_100_historical_records_is_excluded(self):
        history = self._history()[:99]
        prepared = prepare_evaluation(history, [self._evaluation_record()])
        self.assertEqual(prepared, [])

    def test_vehicle_at_100_historical_records_is_evaluable(self):
        prepared = prepare_evaluation(self._history(), [self._evaluation_record()])
        self.assertEqual(len(prepared), 1)

    def test_simple_known_detection(self):
        self.assertTrue(apply_rule(.51, None, "D1", .5, None, None))
        self.assertTrue(apply_rule(.51, 2.1, "D3", .5, 2.0, "AND"))
        self.assertFalse(apply_rule(.51, 2.0, "D3", .5, 2.0, "AND"))

    def test_recall_is_calculated_correctly(self):
        result = rates(10, 8, 10, 2)
        self.assertEqual(result["recall_pct"], 80.0)

    def test_false_positive_rate_is_calculated_correctly(self):
        result = rates(10, 8, 10, 2)
        self.assertEqual(result["false_positive_rate_pct"], 20.0)

    def test_history_and_evaluation_are_temporally_separated(self):
        content = "Codigo Vehiculo;Fecha de inicio;Distancia;Consumo\n1;2024-01-01 00:00:00.000;1000;10,0\n1;2025-01-01 00:00:00.000;1000;10,0\n1;2026-01-01 00:00:00.000;1000;10,0\n1;2027-01-01 00:00:00.000;1000;10,0\n"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.csv"
            source.write_text(content, encoding="utf-8")
            history, evaluation = load_records(source)
        self.assertEqual(len(history), 2)
        self.assertEqual(len(evaluation), 1)
        self.assertEqual(history[0]["l_100km"], 1.0)

    def test_rule_comparison_uses_existing_aggregates(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "summary.csv"
            output = Path(directory) / "comparison.csv"
            fieldnames = ["perturbation_pct", "scenario", "scope", "recall_pct", "false_negative_rate_pct", "false_positive_rate_pct"]
            with source.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for name, *_ in RULES:
                    for level, recall in ((25, 20), (50, 40), (100, 60), (200, 80), (500, 100)):
                        writer.writerow({"perturbation_pct": level, "scenario": name, "scope": "completo", "recall_pct": recall, "false_negative_rate_pct": 100 - recall, "false_positive_rate_pct": 10})
            rows = build_rule_comparison(source, output)
        self.assertEqual(len(rows), 12)
        self.assertEqual(rows[0]["baseline_review_rate"], .1)
        self.assertEqual(rows[0]["baseline_non_review_rate"], .9)
        self.assertEqual(rows[0]["post_perturbation_review_rate_plus_25"], .2)
        self.assertIsNone(rows[0]["incremental_detection_rate_plus_25"])
        self.assertFalse(any("recall" in key or "specificity" in key for key in rows[0]))

    @staticmethod
    def _history():
        return [
            {"vehicle": "1", "range": "<= 1", "l_100km": value}
            for value in ((9.0, 10.0, 11.0) * 33 + (10.0,))
        ]

    @staticmethod
    def _evaluation_record():
        return {
            "vehicle": "1",
            "range": "<= 1",
            "distance_km": 1.0,
            "consumption_liters": .01,
            "l_100km": 1.0,
        }


if __name__ == "__main__":
    unittest.main()
