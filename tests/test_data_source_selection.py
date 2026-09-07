import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.api import build_analytical_service


class DataSourceSelectionTests(unittest.TestCase):
    @patch("src.api.AnalyticalService.from_csv")
    def test_csv_is_default_and_uses_configured_path(self, from_csv):
        expected = MagicMock()
        from_csv.return_value = expected

        result = build_analytical_service({"TFM_DATA_PATH": "custom/history.csv"})

        self.assertIs(result, expected)
        from_csv.assert_called_once_with(Path("custom/history.csv"))

    @patch("src.api.AnalyticalService.from_history")
    @patch("src.api.SqlHistoricalRepository.from_environment")
    def test_sql_loads_repository_rows(self, from_environment, from_history):
        environment = {"TFM_DATA_SOURCE": "sql"}
        rows = [{"Codigo Viaje": "T-1"}]
        from_environment.return_value.load_historical_rows.return_value = rows
        expected = MagicMock()
        from_history.return_value = expected

        result = build_analytical_service(environment)

        self.assertIs(result, expected)
        from_environment.assert_called_once_with(environment)
        from_history.assert_called_once_with(rows)

    def test_sql_reports_missing_environment_variables(self):
        with self.assertRaisesRegex(ValueError, "TFM_DB_SERVER") as raised:
            build_analytical_service({"TFM_DATA_SOURCE": "sql"})
        self.assertNotIn("secret-value", str(raised.exception))

    def test_unknown_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "csv.*sql"):
            build_analytical_service({"TFM_DATA_SOURCE": "unknown"})

    def test_csv_blank_consumption_allows_loading_and_partial_evaluation(self):
        header = "Codigo Viaje;Codigo Vehiculo;Fecha de inicio;Distancia;Consumo;Duracion\n"
        history = "".join(
            f"H{index};V1;2024-01-01;2000;;{(1 + index % 5) * 120}\n"
            for index in range(100)
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trips.csv"
            path.write_text(
                header + history + "T1;V1;2026-01-01;2000;;360\n",
                encoding="utf-8",
            )
            service = build_analytical_service({"TFM_DATA_PATH": str(path)})
            with path.open(encoding="utf-8", newline="") as source:
                trip = list(csv.DictReader(source, delimiter=";"))[-1]
            self.assertEqual(trip["Consumo"], "")
            result = service.evaluate(trip).to_dict()

        self.assertEqual(result["analysis_coverage"], "PARTIAL")
        self.assertEqual(result["overall_status"], "NO_RELEVANT_DEVIATION")
        consumption = result["signals"]["consumption"]
        self.assertEqual(consumption["status"], "NOT_EVALUABLE")
        self.assertEqual(consumption["reason"], "MISSING_CONSUMPTION")
        self.assertIsNone(consumption["consumo_litros"])
        self.assertIsNone(consumption["consumo_l_100km"])
        self.assertEqual(result["signals"]["temporal"]["status"], "NO_RELEVANT_DEVIATION")


if __name__ == "__main__":
    unittest.main()
