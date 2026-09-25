import unittest
from datetime import datetime
from unittest.mock import MagicMock
from decimal import Decimal

from src.data_processing import normalize_trip

from src.sql_repository import (
    DEFAULT_DRIVER,
    ANALYTICAL_ROWS_QUERY,
    HISTORICAL_QUERY,
    TRIP_BY_ID_QUERY,
    SqlHistoricalRepository,
    SqlServerConfig,
)


class SqlHistoricalRepositoryTests(unittest.TestCase):
    def test_all_sql_routes_preserve_ml_before_normalization(self):
        for consumption in (Decimal("4156"), 0, None):
            for route in ("history", "trip", "period", "operational", "vehicle"):
                with self.subTest(consumption=consumption, route=route):
                    repository, cursor, _ = self.make_trip_repository(
                        ("SYNTHETIC", "V-1", datetime(2026, 9, 1), 5725, consumption, 600)
                    )
                    cursor.fetchall.return_value = [cursor.fetchone.return_value]
                    start, end = datetime(2026, 9, 1), datetime(2026, 9, 2)
                    if route == "history":
                        row = repository.load_historical_rows()[0]
                    elif route == "trip":
                        row = repository.get_trip_by_id("SYNTHETIC")
                    elif route == "period":
                        row = repository.load_rows_between(start, end)[0]
                    else:
                        row = repository.load_operational_rows_between(
                            start, end, matricula="TEST001" if route == "vehicle" else None
                        )[0]
                    self.assertEqual(row["Consumo"], None if consumption is None else float(consumption))
                    normalized = normalize_trip(row)
                    if consumption is None:
                        self.assertIsNone(normalized.consumo_litros)
                    else:
                        self.assertAlmostEqual(normalized.consumo_litros, float(consumption) / 1000)
                    if consumption:
                        self.assertAlmostEqual(normalized.consumo_litros, 4.156)
                        self.assertAlmostEqual(normalized.consumo_l_100km, 4.156 / 5.725 * 100)

    def make_trip_repository(self, row):
        columns = (
            "Codigo Viaje", "Codigo Vehiculo", "Fecha de inicio",
            "Distancia", "Consumo", "Duracion",
        )
        cursor = MagicMock()
        cursor.description = [(column,) for column in columns]
        cursor.fetchone.return_value = row
        connection = MagicMock()
        connection.cursor.return_value = cursor
        repository = SqlHistoricalRepository(
            SqlServerConfig("server", "database", "user", "secret"),
            connection_factory=MagicMock(return_value=connection),
        )
        return repository, cursor, connection

    def test_get_trip_by_id_finds_and_normalizes_trip_with_parameterized_query(self):
        repository, cursor, connection = self.make_trip_repository(
            ("14214132008", "V-1", datetime(2026, 8, 1, 10), 2000, 675, 600)
        )

        trip = repository.get_trip_by_id("14214132008")

        self.assertEqual(trip["Codigo Viaje"], "14214132008")
        self.assertEqual(trip["Consumo"], 675.0)
        cursor.execute.assert_called_once_with(TRIP_BY_ID_QUERY, "14214132008")
        self.assertIn("?", TRIP_BY_ID_QUERY)
        self.assertNotIn("14214132008", TRIP_BY_ID_QUERY)
        connection.close.assert_called_once_with()

    def test_get_trip_by_id_preserves_null_consumption(self):
        repository, _, _ = self.make_trip_repository(
            ("T-NULL", "V-1", datetime(2026, 8, 1), 2000, None, 600)
        )
        self.assertIsNone(repository.get_trip_by_id("T-NULL")["Consumo"])

    def test_get_trip_by_id_returns_none_when_trip_does_not_exist(self):
        repository, _, connection = self.make_trip_repository(None)
        self.assertIsNone(repository.get_trip_by_id("missing"))
        connection.close.assert_called_once_with()

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

        sql_rows = [sql_row("T-1", 675), sql_row("T-2", 0), sql_row("T-3", None)]
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

    def test_load_rows_between_uses_one_parameterized_bulk_query(self):
        columns = (
            "Codigo Viaje", "Codigo Vehiculo", "Fecha de inicio",
            "Distancia", "Consumo", "Duracion",
        )
        cursor = MagicMock()
        cursor.description = [(column,) for column in columns]
        cursor.fetchall.return_value = [
            ("T-2026", "V-1", datetime(2026, 6, 1), 2000, 500, 600)
        ]
        connection = MagicMock()
        connection.cursor.return_value = cursor
        repository = SqlHistoricalRepository(
            SqlServerConfig("server", "database", "user", "secret"),
            connection_factory=MagicMock(return_value=connection),
        )

        start = datetime(2026, 3, 1)
        end = datetime(2026, 4, 1)
        rows = repository.load_rows_between(start, end)

        self.assertEqual(rows[0]["Consumo"], 500.0)
        cursor.execute.assert_called_once_with(
            ANALYTICAL_ROWS_QUERY,
            start,
            end,
        )
        self.assertNotIn("SELECT *", ANALYTICAL_ROWS_QUERY.upper())
        connection.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
