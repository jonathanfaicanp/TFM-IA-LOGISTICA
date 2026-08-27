import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_b30_2026_deviations import pct_above, summary_row


class AnalyzeB30DeviationsTests(unittest.TestCase):
    def test_percentages_use_strictly_greater_than_threshold(self):
        self.assertEqual(pct_above([0.5, 0.5001, 1.0], 0.5), 66.66666667)

    def test_summary_contains_only_aggregates(self):
        row = summary_row("11", [0.0, 1.0, 2.0, 6.0], "codigo_vehiculo")
        self.assertEqual(row["registros_evaluables"], 4)
        self.assertEqual(row["porcentaje_over_100pct"], 50.0)
        self.assertNotIn("baseline", row)
        self.assertNotIn("l_100km", row)


if __name__ == "__main__":
    unittest.main()
