import unittest
from unittest.mock import MagicMock

import httpx

from src.analytical_service import AnalyticalService
from src.api import create_app
from src.models import DetectionStatus


def historical_row(index):
    distance = 2000
    consumption = (80, 90, 100, 110, 120)[index % 5]
    minutes_per_km = (1, 2, 3, 4, 5)[index % 5]
    return {
        "Codigo Viaje": f"H{index}",
        "Codigo Vehiculo": "V1",
        "Fecha de inicio": "2024-01-01",
        "Distancia": distance,
        "Consumo": consumption,
        "Duracion": minutes_per_km * (distance / 1000) * 60,
    }


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.service = AnalyticalService.from_history(historical_row(index) for index in range(100))
        self.app = create_app(service=self.service)
        self.lifespan = self.app.router.lifespan_context(self.app)
        await self.lifespan.__aenter__()
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test")

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)

    async def test_health(self):
        response = await self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    async def test_valid_evaluation_returns_consolidated_result(self):
        response = await self.client.post("/evaluate", json={
            "trip_id": "SYNTHETIC-1",
            "vehicle_id": "V1",
            "timestamp": "2026-01-01T12:00:00",
            "distance_m": 2000,
            "consumption_ml": 400,
            "duration_seconds": 720,
        })
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["overall_status"], "REVIEW")
        self.assertEqual(body["analysis_coverage"], "COMPLETE")
        self.assertEqual(body["review_signals"], ["consumption", "temporal"])
        self.assertEqual(set(body["signals"]), {"consumption", "temporal"})

    async def test_invalid_request_is_rejected(self):
        missing = await self.client.post("/evaluate", json={"trip_id": "SYNTHETIC-2"})
        forbidden = await self.client.post("/evaluate", json={
            "trip_id": "SYNTHETIC-2", "vehicle_id": "V1",
            "timestamp": "2026-01-01T12:00:00", "distance_m": 2000,
            "consumption_ml": 400, "duration_seconds": 720,
            "overall_status": "REVIEW",
        })
        self.assertEqual(missing.status_code, 422)
        self.assertEqual(forbidden.status_code, 422)

    async def test_detector_regressions_through_service(self):
        row = {
            "Codigo Viaje": "SYNTHETIC-3", "Codigo Vehiculo": "V1",
            "Fecha de inicio": "2026-01-01", "Distancia": 2000,
            "Consumo": 400, "Duracion": 720,
        }
        self.assertEqual(self.service.consumption_detector.evaluate(row).status, DetectionStatus.REVIEW)
        self.assertEqual(self.service.temporal_detector.evaluate(row).status, DetectionStatus.REVIEW)

    async def test_evaluate_trip_is_unavailable_in_csv_mode(self):
        response = await self.client.post("/evaluate-trip", json={"trip_id": "T-1"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("TFM_DATA_SOURCE=sql", response.json()["detail"])

    async def test_evaluate_endpoint_still_works_after_adding_operational_endpoint(self):
        response = await self.client.post("/evaluate", json={
            "trip_id": "SYNTHETIC-4", "vehicle_id": "V1",
            "timestamp": "2026-01-01T12:00:00", "distance_m": 2000,
            "consumption_ml": 400, "duration_seconds": 720,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["trip_id"], "SYNTHETIC-4")


class SqlTripApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        service = AnalyticalService.from_history(historical_row(index) for index in range(100))
        self.repository = MagicMock()
        self.repository.get_trip_by_id.return_value = {
            "Codigo Viaje": "14214132008", "Codigo Vehiculo": "V1",
            "Fecha de inicio": "2026-01-01 12:00:00", "Distancia": 2000,
            "Consumo": 400, "Duracion": 720,
        }
        self.app = create_app(service=service, repository=self.repository, data_source="sql")
        self.lifespan = self.app.router.lifespan_context(self.app)
        await self.lifespan.__aenter__()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app), base_url="http://test"
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)

    async def test_evaluate_trip_uses_repository_and_returns_consolidated_result(self):
        response = await self.client.post("/evaluate-trip", json={"trip_id": "14214132008"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["trip_id"], "14214132008")
        self.assertEqual(set(response.json()["signals"]), {"consumption", "temporal"})
        self.repository.get_trip_by_id.assert_called_once_with("14214132008")

    async def test_evaluate_trip_returns_404_for_unknown_trip(self):
        self.repository.get_trip_by_id.return_value = None
        response = await self.client.post("/evaluate-trip", json={"trip_id": "missing"})
        self.assertEqual(response.status_code, 404)
        self.assertIn("missing", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
