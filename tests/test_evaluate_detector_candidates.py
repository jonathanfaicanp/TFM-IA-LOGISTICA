import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluate_detector_candidates import applicable_records, relative_deviation, rule_and, rule_or
from analyze_b30_mad import robust_z


class EvaluateDetectorCandidatesTests(unittest.TestCase):
    def test_relative_deviation(self):
        self.assertEqual(relative_deviation(15.0, 10.0), 0.5)

    def test_robust_z(self):
        self.assertAlmostEqual(robust_z(4.4826, 3.0, 1.4826), 1.0)

    def test_and_rule_requires_both_conditions(self):
        self.assertTrue(rule_and(1.1, 3.1, 1.0, 3.0))
        self.assertFalse(rule_and(1.1, 3.0, 1.0, 3.0))

    def test_or_rule_accepts_either_condition(self):
        self.assertTrue(rule_or(0.1, 3.1, 1.0, 3.0))
        self.assertTrue(rule_or(1.1, 0.1, 1.0, 3.0))
        self.assertFalse(rule_or(1.0, 3.0, 1.0, 3.0))

    def test_thresholds_are_strictly_greater_than(self):
        self.assertFalse(rule_and(0.5, 2.1, 0.5, 2.0))
        self.assertFalse(rule_or(0.5, 2.0, 0.5, 2.0))

    def test_records_without_robust_z_are_excluded_from_d2_d3(self):
        records = [{"relative": 10.0, "robust_z": None}, {"relative": 0.0, "robust_z": 1.0}]
        self.assertEqual(len(applicable_records(records, "D1")), 2)
        self.assertEqual(len(applicable_records(records, "D2")), 1)
        self.assertEqual(len(applicable_records(records, "D3")), 1)


if __name__ == "__main__":
    unittest.main()
