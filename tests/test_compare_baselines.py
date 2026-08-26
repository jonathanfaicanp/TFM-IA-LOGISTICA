import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare_baselines import distance_range, parse_number, parse_start_date


class CompareBaselinesTests(unittest.TestCase):
    def test_spanish_decimal_conversion(self):
        self.assertEqual(parse_number("7,5"), 7.5)
        self.assertEqual(parse_number("1.234,5"), 1234.5)

    def test_unit_conversion_and_l_100km(self):
        distance_km = 25_000 / 1000
        consumption_liters = 7_500 / 1000
        self.assertEqual(distance_km, 25)
        self.assertEqual(consumption_liters, 7.5)
        self.assertEqual(consumption_liters / distance_km * 100, 30)

    def test_distance_ranges(self):
        expected = ["<= 1", "> 1 y <= 2", "> 2 y <= 5", "> 5 y <= 10", "> 10 y <= 20", "> 20 y <= 50", "> 50 y <= 100", "> 100 y <= 300", "> 300"]
        values = [1, 1.01, 2.01, 5.01, 10.01, 20.01, 50.01, 100.01, 300.01]
        self.assertEqual([distance_range(value) for value in values], expected)

    def test_temporal_window_2024_2025(self):
        dates = [parse_start_date("2023-12-31 00:00:00.000"), parse_start_date("2024-01-01 00:00:00.000"), parse_start_date("2025-12-31 00:00:00.000"), parse_start_date("2026-01-01 00:00:00.000")]
        included = [date for date in dates if date.year in (2024, 2025)]
        self.assertEqual(included, [datetime(2024, 1, 1), datetime(2025, 12, 31)])


if __name__ == "__main__":
    unittest.main()
