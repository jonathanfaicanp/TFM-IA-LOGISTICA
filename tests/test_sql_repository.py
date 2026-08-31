import unittest
from datetime import datetime
from unittest.mock import MagicMock

from src.sql_repository import (
    DEFAULT_DRIVER,
    HISTORICAL_QUERY,
    SqlHistoricalRepository,
    SqlServerConfig,
)


class SqlHistoricalRepositoryTests(unittest.TestCase):
    def test_load_historical_rows_preserves_analytical_column_contract(self):
        columns = (
            "Codigo Viaje", "Codigo Vehiculo", "Nombre Vehiculo", "Fecha de inicio",
            "Duracion", "Distancia", "Velocidad maxima", "Consumo",
            "Indicador de conduccion",
        )
        def sql_row(trip_id, consumption):
            return (
                trip_id, "V-1", "Camión 1", datetime(2024, 6, 15, 8, 30),
                600, 10538, 83.5, consumption, 91,
            )

        sql_rows = [sql_row("T-1", 0.675), sql_row("T-2", 0), sql_row("T-3", None)]
        cursor = MagicMock()
        cursor.description = [(column,) for column in columns]
        cursor.fetchall.return_value = sql_rows
        connection = MagicMock()
        connection.cursor.return_value = cursor
        factory = MagicMock(return_value=connection)
        config = SqlServerConfig("server", "database", "user", "secret")

        rows = SqlHistoricalRepository(config, connection_factory=factory).load_historical_rows()

        self.assertEqual(
            [row["Consumo"] for row in rows],
            [675.0, 0.0, None],
        )
        cursor.execute.assert_called_once_with(
            HISTORICAL_QUERY, datetime(2024, 1, 1), datetime(2026, 1, 1)
        )
        self.assertNotIn("SELECT *", HISTORICAL_QUERY.upper())
        connection.close.assert_called_once_with()

    def test_default_driver_and_missing_configuration(self):
        environment = {
            "TFM_DB_SERVER": "server",
            "TFM_DB_DATABASE": "database",
            "TFM_DB_USER": "user",
            "TFM_DB_PASSWORD": "secret-value",
        }
        self.assertEqual(SqlServerConfig.from_environment(environment).driver, DEFAULT_DRIVER)

        del environment["TFM_DB_USER"]
        del environment["TFM_DB_PASSWORD"]
        with self.assertRaisesRegex(
            ValueError, "TFM_DB_USER, TFM_DB_PASSWORD"
        ) as raised:
            SqlServerConfig.from_environment(environment)
        self.assertNotIn("secret-value", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
