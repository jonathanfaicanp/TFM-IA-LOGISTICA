import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_distance_threshold_sensitivity import b30_deviation, scenario_summary


class DistanceThresholdSensitivityTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            {"vehicle": "1", "distance_km": 0.5, "range": "<= 1", "l_100km": 20.0},
            {"vehicle": "1", "distance_km": 1.0, "range": "<= 1", "l_100km": 10.0},
            {"vehicle": "1", "distance_km": 1.1, "range": "> 1 y <= 2", "l_100km": 15.0},
        ]
        self.vehicles = {"1": 10.0}
        self.contexts = {("1", "<= 1"): (12.0, 30)}

    def test_distance_filter_is_strictly_greater_than(self):
        summary, _ = scenario_summary("gt_1", 1.0, self.records, self.vehicles, self.contexts)
        self.assertEqual(summary["records_after_distance_filter"], 1)
        self.assertEqual(summary["records_discarded_by_filter"], 2)

    def test_b30_context_and_vehicle_fallback(self):
        self.assertAlmostEqual(b30_deviation(self.records[0], self.vehicles, self.contexts), 20 / 12 - 1)
        self.assertEqual(b30_deviation(self.records[2], self.vehicles, self.contexts), 0.5)


if __name__ == "__main__":
    unittest.main()
