import unittest
from datetime import datetime
from unittest.mock import MagicMock

from src.sql_repository import (
    OPERATIONAL_PERIOD_QUERY, VEHICLE_PERIOD_QUERY,
    SqlHistoricalRepository, SqlServerConfig,
)
from src.analytical_service import AnalyticalService


class OperationalRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.cursor = MagicMock()
        self.cursor.description = [(name,) for name in (
            "Codigo Viaje", "Codigo Vehiculo", "matricula", "Fecha de inicio",
            "Distancia", "Consumo", "Duracion",
        )]
        self.cursor.fetchall.return_value = [
            ("T1", "INTERNAL-1", "TEST001", datetime(2026, 9, 7, 23, 59, 59), 2000, 0.4, 720)
        ]
        self.connection = MagicMock()
        self.connection.cursor.return_value = self.cursor
        self.factory = MagicMock(return_value=self.connection)
        self.repository = SqlHistoricalRepository(
            SqlServerConfig("test", "test", "test", "test"), connection_factory=self.factory
        )
        self.start, self.end = datetime(2026, 9, 1), datetime(2026, 9, 8)

    def test_vehicle_parameterization_and_identity(self):
        plate = "TEST001' OR 1=1 --"
        rows = self.repository.load_operational_rows_between(self.start, self.end, matricula=plate)
        self.cursor.execute.assert_called_once_with(VEHICLE_PERIOD_QUERY, 1001, self.start, self.end, plate)
        self.assertNotIn(plate, VEHICLE_PERIOD_QUERY)
        self.assertIn("[Nombre Vehiculo] = ?", VEHICLE_PERIOD_QUERY)
        self.assertEqual(rows[0]["Codigo Vehiculo"], "INTERNAL-1")
        self.assertEqual(rows[0]["matricula"], "TEST001")
        self.assertEqual(rows[0]["Consumo"], 400)
        self.connection.close.assert_called_once_with()

    def test_global_query_is_bounded_and_parameterized(self):
        self.repository.load_operational_rows_between(self.start, self.end, limit=10)
        self.cursor.execute.assert_called_once_with(OPERATIONAL_PERIOD_QUERY, 10, self.start, self.end)
        for query in (OPERATIONAL_PERIOD_QUERY, VEHICLE_PERIOD_QUERY):
            self.assertIn("[Nombre Vehiculo] AS [matricula]", query)
            self.assertNotIn("[Matricula]", query)
            self.assertIn("TOP (?)", query)
            self.assertIn("[Fecha de inicio] >= ?", query)
            self.assertIn("[Fecha de inicio] < ?", query)
            self.assertNotIn("Conductor", query)
            self.assertNotIn("SELECT *", query)
            self.assertNotIn("REVIEW", query)
        self.connection.close.assert_called_once_with()

    def test_no_trips(self):
        self.cursor.fetchall.return_value = []
        self.assertEqual(self.repository.load_operational_rows_between(self.start, self.end, matricula="MISSING"), [])

    def test_same_plate_preserves_each_vehicle_code(self):
        self.cursor.fetchall.return_value = [
            ("T1", "INTERNAL-1", "TEST001", self.start, 2000, 0.4, 720),
            ("T2", "INTERNAL-2", "TEST001", self.start, 2000, 0.4, 720),
        ]
        rows = self.repository.load_operational_rows_between(
            self.start, self.end, matricula="TEST001"
        )
        self.assertEqual([row["matricula"] for row in rows], ["TEST001", "TEST001"])
        self.assertEqual([row["Codigo Vehiculo"] for row in rows], ["INTERNAL-1", "INTERNAL-2"])

    def test_missing_consumption_preserved(self):
        self.cursor.fetchall.return_value = [
            ("T1", "INTERNAL-1", "TEST001", self.start, 2000, None, 720)
        ]
        self.assertIsNone(self.repository.load_operational_rows_between(self.start, self.end)[0]["Consumo"])

    def test_invalid_bounds_and_limits_do_not_connect(self):
        for limit in (0, -1, 1002):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                self.repository.load_operational_rows_between(self.start, self.end, limit=limit)
        for end in (self.start, datetime(2026, 8, 31)):
            with self.subTest(end=end), self.assertRaises(ValueError):
                self.repository.load_operational_rows_between(self.start, end)
        self.factory.assert_not_called()

    def test_connection_closed_on_query_failure(self):
        self.cursor.execute.side_effect = RuntimeError("simulated")
        with self.assertRaises(RuntimeError):
            self.repository.load_operational_rows_between(self.start, self.end)
        self.connection.close.assert_called_once_with()

    def test_sql_rows_use_vehicle_code_for_real_motor_baseline(self):
        history = [{
            "Codigo Viaje": f"H{i}", "Codigo Vehiculo": "INTERNAL-1",
            "Fecha de inicio": "2024-01-01", "Distancia": 2000,
            "Consumo": (80, 90, 100, 110, 120)[i % 5],
            "Duracion": (1 + i % 5) * 120,
        } for i in range(100)]
        service = AnalyticalService.from_history(history)
        row = self.repository.load_operational_rows_between(self.start, self.end, matricula="TEST001")[0]
        result = service.evaluate(row).to_dict()
        self.assertEqual(result["vehicle_id"], "INTERNAL-1")
        self.assertEqual(result["overall_status"], "REVIEW")
        row["matricula"] = "DIFFERENT-PLATE"
        self.assertEqual(service.evaluate(row).to_dict(), result)
