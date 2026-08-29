import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_temporal_robustness import build_scopes, candidate_rates, median_mad, robust_z, select_scope


class TemporalRobustnessTests(unittest.TestCase):
    def test_median_mad_and_robust_z(self):
        centre, mad = median_mad([1, 2, 3, 4, 5])
        self.assertEqual((centre, mad), (3, 1))
        self.assertAlmostEqual(robust_z(4.4826, centre, mad), 1)
        self.assertIsNone(robust_z(4, centre, 0))

    def test_contextual_scope_and_vehicle_fallback(self):
        context = [{"vehicle": "1", "range": "<= 1", "minutes_per_km": 1 + index / 100} for index in range(30)]
        remainder = [{"vehicle": "1", "range": "> 1 y <= 2", "minutes_per_km": 2 + index / 100} for index in range(70)]
        vehicles, contexts = build_scopes(context + remainder)
        self.assertEqual(select_scope(context[0], vehicles, contexts)[3], "contextual")
        self.assertEqual(select_scope({"vehicle": "1", "range": "> 300"}, vehicles, contexts)[3], "vehicle_fallback")

    def test_vehicle_below_100_is_not_eligible(self):
        records = [{"vehicle": "1", "range": "<= 1", "minutes_per_km": 1 + index / 100} for index in range(99)]
        vehicles, contexts = build_scopes(records)
        self.assertEqual((vehicles, contexts), ({}, {}))

    def test_candidate_rules_are_strict_and_upper_tail_only(self):
        records = [
            {"relative_deviation": .50, "robust_z": 3},
            {"relative_deviation": .51, "robust_z": 2},
            {"relative_deviation": .51, "robust_z": 2.01},
            {"relative_deviation": -2, "robust_z": -10},
        ]
        rates = candidate_rates(records)
        self.assertEqual(rates["relative_gt_50pct_AND_z_gt_2"], 25.0)


if __name__ == "__main__":
    unittest.main()
