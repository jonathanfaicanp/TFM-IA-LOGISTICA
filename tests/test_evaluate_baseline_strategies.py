import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluate_baseline_strategies import build_baselines, evaluate_strategy


class EvaluateBaselineStrategiesTests(unittest.TestCase):
    def setUp(self):
        self.construction = [
            {"vehicle": "1", "range": "<= 1", "l_100km": 10.0},
            {"vehicle": "1", "range": "<= 1", "l_100km": 14.0},
            {"vehicle": "1", "range": "> 20 y <= 50", "l_100km": 6.0},
        ]

    def test_baselines_are_built_only_from_construction(self):
        vehicle, context = build_baselines(self.construction)
        self.assertEqual(vehicle["1"], 10.0)
        self.assertEqual(context[("1", "<= 1")], (12.0, 2))

    def test_b30_uses_vehicle_fallback_for_small_context(self):
        vehicle, context = build_baselines(self.construction)
        evaluation = [{"vehicle": "1", "range": "<= 1", "l_100km": 15.0}]
        summary, _ = evaluate_strategy("B30", 30, evaluation, vehicle, context)
        self.assertEqual(summary["fallback_evaluations"], 1)
        self.assertEqual(summary["contextual_evaluations"], 0)
        self.assertEqual(summary["relative_deviation"]["median"], 0.5)

    def test_b30_uses_context_when_minimum_is_met(self):
        construction = [{"vehicle": "1", "range": "<= 1", "l_100km": 10.0} for _ in range(30)]
        vehicle, context = build_baselines(construction)
        summary, _ = evaluate_strategy("B30", 30, [{"vehicle": "1", "range": "<= 1", "l_100km": 15.0}], vehicle, context)
        self.assertEqual(summary["contextual_evaluations"], 1)
        self.assertEqual(summary["fallback_evaluations"], 0)
        self.assertEqual(summary["relative_deviation"]["median"], 0.5)


if __name__ == "__main__":
    unittest.main()
