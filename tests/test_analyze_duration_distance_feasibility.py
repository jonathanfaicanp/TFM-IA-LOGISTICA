import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_duration_distance_feasibility import absolute_median_change_pct, summarize, transform_duration_distance


class DurationDistanceFeasibilityTests(unittest.TestCase):
    def test_duration_distance_transformations(self):
        distance_km, duration_minutes, minutes_per_km = transform_duration_distance(600, 5_000)
        self.assertEqual((distance_km, duration_minutes, minutes_per_km), (5.0, 10.0, 2.0))

    def test_distribution_summary(self):
        result = summarize([1, 2, 3, 4, 5])
        self.assertEqual(result, {"n": 5, "median": 3, "p25": 2, "p75": 4, "p90": 4.6, "p95": 4.8, "p99": 4.96})

    def test_absolute_median_change(self):
        self.assertEqual(absolute_median_change_pct([8, 10, 12], [9, 12, 15]), 20.0)


if __name__ == "__main__":
    unittest.main()
