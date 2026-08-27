import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_b30_mad import MAD_SCALE, load_records, median_mad, robust_z


class AnalyzeB30MadTests(unittest.TestCase):
    def test_mad_and_scaled_mad(self):
        centre, mad, scale = median_mad([1.0, 2.0, 3.0, 4.0, 100.0])
        self.assertEqual(centre, 3.0)
        self.assertEqual(mad, 1.0)
        self.assertEqual(scale, MAD_SCALE)

    def test_robust_z(self):
        self.assertAlmostEqual(robust_z(4.4826, 3.0, 1.4826), 1.0)

    def test_zero_mad_has_no_score(self):
        centre, mad, scale = median_mad([2.0, 2.0, 2.0])
        self.assertEqual((centre, mad, scale), (2.0, 0.0, 0.0))
        self.assertIsNone(robust_z(3.0, centre, scale))

    def test_load_records_separates_history_and_2026(self):
        content = "Codigo Vehiculo;Fecha de inicio;Distancia;Consumo\n1;2024-01-01 00:00:00.000;1000;10,0\n1;2025-01-01 00:00:00.000;1000;10,0\n1;2026-01-01 00:00:00.000;1000;10,0\n1;2027-01-01 00:00:00.000;1000;10,0\n"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.csv"
            source.write_text(content, encoding="utf-8")
            history, evaluation = load_records(source)
        self.assertEqual(len(history), 2)
        self.assertEqual(len(evaluation), 1)


if __name__ == "__main__":
    unittest.main()
