import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluate_temporal_synthetic_benchmark import aggregate_rates, normalize_temporal_record, perturb_record


def row(distance, duration=600):
    return {"Codigo Vehiculo": "1", "Fecha de inicio": "2026-01-01", "Duracion": str(duration), "Distancia": str(distance)}


class TemporalSyntheticBenchmarkTests(unittest.TestCase):
    def test_trips_at_or_below_one_km_are_excluded(self):
        self.assertIsNone(normalize_temporal_record(row(1000)))
        self.assertIsNone(normalize_temporal_record(row(999)))
        self.assertIsNotNone(normalize_temporal_record(row(1001)))

    def test_duration_perturbation_keeps_distance_and_recalculates_minutes_per_km(self):
        source = normalize_temporal_record(row(5000, 600))
        perturbed = perturb_record(source, .5)
        self.assertEqual(perturbed["duration_minutes"], 15)
        self.assertEqual(perturbed["distance_km"], 5)
        self.assertEqual(perturbed["minutes_per_km"], 3)
        self.assertEqual(source["duration_minutes"], 10)

    def test_critical_aggregate_metrics(self):
        result = aggregate_rates(10, 8, 10, 2)
        self.assertEqual(result["recall_pct"], 80)
        self.assertEqual(result["false_negative_rate_pct"], 20)
        self.assertEqual(result["control_marked_pct_experimental"], 20)
        self.assertEqual(result["specificity_pct_experimental"], 80)
        self.assertEqual(result["balanced_accuracy_pct"], 80)
        self.assertEqual(result["youden_j_pct_points"], 60)


if __name__ == "__main__":
    unittest.main()
