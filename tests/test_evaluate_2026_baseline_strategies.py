import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluate_2026_baseline_strategies import build_baselines, evaluate


class Evaluate2026StrategiesTests(unittest.TestCase):
    def setUp(self):
        self.history = [{"vehicle": "1", "range": "<= 1", "l_100km": 10.0} for _ in range(30)]
        self.vehicle, self.context = build_baselines(self.history)

    def test_contextual_baseline_uses_history_count(self):
        summary, _, _ = evaluate("B30", 30, [{"vehicle": "1", "range": "<= 1", "l_100km": 15.0}], self.vehicle, self.context)
        self.assertEqual(summary["records_evaluable"], 1)
        self.assertEqual(summary["contextual_evaluations_pct"], 100.0)
        self.assertEqual(summary["deviation_median"], 0.5)

    def test_fallback_when_context_is_small(self):
        summary, _, _ = evaluate("B50", 50, [{"vehicle": "1", "range": "<= 1", "l_100km": 15.0}], self.vehicle, self.context)
        self.assertEqual(summary["fallback_evaluations_pct"], 100.0)
        self.assertEqual(summary["deviation_median"], 0.5)

    def test_no_baseline_is_not_evaluable(self):
        summary, _, _ = evaluate("A", None, [{"vehicle": "unknown", "range": "<= 1", "l_100km": 15.0}], self.vehicle, self.context)
        self.assertEqual(summary["records_evaluable"], 0)
        self.assertEqual(summary["records_without_baseline"], 1)
        self.assertEqual(summary["coverage_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
