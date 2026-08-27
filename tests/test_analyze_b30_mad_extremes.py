import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_b30_mad_extremes import aggregate, minimal_vehicles_for_half


class AnalyzeB30MadExtremesTests(unittest.TestCase):
    def test_minimal_vehicles_for_half(self):
        records = [{"vehicle": "1"}] * 4 + [{"vehicle": "2"}] * 3 + [{"vehicle": "3"}] * 3
        self.assertEqual(minimal_vehicles_for_half(records), 2)

    def test_aggregate_is_aggregate_only(self):
        records = [{"vehicle": "1", "distance_m": 1000.0, "consumption_liters": 2.0, "duration_s": 30.0, "max_speed": 40.0, "driving_indicator": .8, "l_100km": 200.0}]
        row = aggregate("robust_z_gt_3", records, 10)
        self.assertEqual(row["porcentaje_sobre_evaluables"], 10.0)
        self.assertEqual(row["vehiculos_implicados"], 1)
        self.assertNotIn("robust_z", row)
        self.assertNotIn("vehicle", row)


if __name__ == "__main__":
    unittest.main()
