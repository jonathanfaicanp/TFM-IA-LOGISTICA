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


if __name__ == "__main__":
    unittest.main()
