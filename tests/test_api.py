import unittest

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


if __name__ == "__main__":
    unittest.main()
