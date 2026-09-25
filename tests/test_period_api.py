import unittest
from datetime import datetime
from unittest.mock import MagicMock

import httpx

from src.analytical_service import AnalyticalService
from src.api import MAX_PERIOD_TRIPS, create_app, normalize_operational_registration


def history(index):
    return {
        "Codigo Viaje": f"H{index}", "Codigo Vehiculo": "V1",
        "Fecha de inicio": "2024-01-01", "Distancia": 2000,
        "Consumo": (80, 90, 100, 110, 120)[index % 5],
        "Duracion": (1 + index % 5) * 120,
    }


def trip(identifier, plate="0001ABC", consumption=100, duration=360, vehicle="V1"):
    return {
        "Codigo Viaje": identifier, "Codigo Vehiculo": vehicle,
        "Fecha de inicio": "2026-09-07 23:59:59", "Distancia": 2000,
        "Consumo": consumption, "Duracion": duration, "matricula": plate,
        "Conductor": "MUST_NOT_BE_RETURNED",
    }


class PeriodApiTests(unittest.IsolatedAsyncioTestCase):
    def test_registration_format(self):
        cases = {
            "2787MGT": "2787MGT", "0599MXZ": "0599MXZ", "9177NBC": "9177NBC",
            "CAMION PLATAFORMA": None, "FURGONETA": None, "MW5422I02463": None,
            "BAJA RA - 0352MXT": None, " 2787MGT ": "2787MGT",
            "0599mxz": "0599MXZ", "2787 MGT": None, "": None, None: None,
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(normalize_operational_registration(value), expected)

    async def test_global_format_filter_preserves_analytical_results(self):
        rows = [trip(str(i), plate, consumption=400) for i, plate in enumerate([
            "2787MGT", " 2787mgt ", "0599MXZ", "CAMION PLATAFORMA",
            " camion plataforma ", "FURGONETA", "MW5422I02463", "BAJA RA - 0352MXT",
        ])]
        rows.append(trip("normal", "OTHER"))
        expected = [self.service.evaluate(row).to_dict() for row in rows]
        self.repository.load_operational_rows_between.return_value = rows
        response = await self.client.post("/review-vehicles-period", json=self.period)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status_counts"]["REVIEW"], 8)
        self.assertEqual(body["total_trips"], 9)
        self.assertEqual(body["excluded_review_trips"], 5)
        self.assertEqual(body["excluded_review_identifiers"], 4)
        self.assertEqual(body["vehicles"], [
            {"matricula": "0599MXZ", "review_count": 1, "trip_ids": ["2"]},
            {"matricula": "2787MGT", "review_count": 2, "trip_ids": ["0", "1"]},
        ])
        self.assertEqual([self.service.evaluate(row).to_dict() for row in rows], expected)
        self.assertNotIn("CAMION PLATAFORMA", response.text)

    async def test_individual_query_still_accepts_non_registration(self):
        row = trip("R", "CAMION PLATAFORMA", consumption=400)
        self.repository.load_operational_rows_between.return_value = [row]
        response = await self.client.post("/evaluate-vehicle-period", json={
            **self.period, "matricula": "CAMION PLATAFORMA"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [self.service.evaluate(row).to_dict()])
        self.assertEqual(self.repository.load_operational_rows_between.call_args.kwargs["matricula"], "CAMION PLATAFORMA")

    async def asyncSetUp(self):
        self.repository = MagicMock()
        self.repository.load_operational_rows_between.return_value = []
        self.service = AnalyticalService.from_history(history(i) for i in range(100))
        self.app = create_app(service=self.service, repository=self.repository, data_source="sql")
        self.lifespan = self.app.router.lifespan_context(self.app)
        await self.lifespan.__aenter__()
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test")
        self.period = {"start_date": "2026-09-01", "end_date": "2026-09-07"}

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)

    async def test_vehicle_preserves_all_states_and_coverage(self):
        self.repository.load_operational_rows_between.return_value = [
            trip("R", consumption=400, duration=720), trip("N"),
            trip("U", vehicle="UNKNOWN"), trip("P", consumption=None),
        ]
        response = await self.client.post("/evaluate-vehicle-period", json={**self.period, "matricula": "0001ABC"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status_counts"], {"REVIEW": 1, "NO_RELEVANT_DEVIATION": 2, "NOT_EVALUABLE": 1})
        self.assertEqual(body["coverage_counts"], {"COMPLETE": 2, "PARTIAL": 1, "NONE": 1})
        self.assertEqual(body["total_trips"], 4)
        self.assertEqual(len(body["results"]), 4)
        self.assertNotIn("Conductor", response.text)
        self.assertNotIn("MUST_NOT_BE_RETURNED", response.text)
        self.repository.load_operational_rows_between.assert_called_once_with(
            datetime(2026, 9, 1), datetime(2026, 9, 8), matricula="0001ABC", limit=1001
        )

    async def test_vehicle_without_trips_returns_empty_result(self):
        response = await self.client.post("/evaluate-vehicle-period", json={**self.period, "matricula": "MISSING"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])
        self.assertEqual(response.json()["total_trips"], 0)

    async def test_global_period_groups_only_motor_reviews(self):
        self.repository.load_operational_rows_between.return_value = [
            trip("R1", "0002ABC", consumption=400), trip("R2", "0002ABC", duration=1200),
            trip("R3", "0001ABC", consumption=400), trip("N", "0003ABC"),
            trip("U", "0004ABC", vehicle="UNKNOWN"),
        ]
        response = await self.client.post("/review-vehicles-period", json=self.period)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_trips"], 5)
        self.assertEqual(body["status_counts"], {"REVIEW": 3, "NO_RELEVANT_DEVIATION": 1, "NOT_EVALUABLE": 1})
        self.assertEqual(body["vehicles"], [
            {"matricula": "0001ABC", "review_count": 1, "trip_ids": ["R3"]},
            {"matricula": "0002ABC", "review_count": 2, "trip_ids": ["R1", "R2"]},
        ])
        self.repository.load_operational_rows_between.assert_called_once_with(
            datetime(2026, 9, 1), datetime(2026, 9, 8), matricula=None, limit=1001
        )

    async def test_global_empty(self):
        response = await self.client.post("/review-vehicles-period", json=self.period)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["vehicles"], [])

    async def test_same_plate_uses_each_vehicle_baseline_before_grouping(self):
        historical_rows = [history(i) for i in range(100)]
        historical_rows += [
            {**history(i), "Codigo Vehiculo": "V2", "Consumo": history(i)["Consumo"] * 4}
            for i in range(100)
        ]
        service = AnalyticalService.from_history(historical_rows)
        self.app.state.analytical_service = service
        rows = [
            trip("R1", consumption=400, vehicle="V1"),
            trip("N2", consumption=400, vehicle="V2"),
            trip("R2", consumption=1600, vehicle="V2"),
        ]
        self.repository.load_operational_rows_between.return_value = rows
        expected = [service.evaluate(row).to_dict() for row in rows]
        self.assertEqual([r["vehicle_id"] for r in expected], ["V1", "V2", "V2"])
        self.assertEqual([r["overall_status"] for r in expected],
                         ["REVIEW", "NO_RELEVANT_DEVIATION", "REVIEW"])
        response = await self.client.post(
            "/evaluate-vehicle-period", json={**self.period, "matricula": "0001ABC"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], expected)
        response = await self.client.post("/review-vehicles-period", json=self.period)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["vehicles"], [
            {"matricula": "0001ABC", "review_count": 2, "trip_ids": ["R1", "R2"]}
        ])
        self.assertEqual(response.json()["status_counts"]["NO_RELEVANT_DEVIATION"], 1)
        self.assertEqual([service.evaluate(row).to_dict() for row in rows], expected)

    async def test_invalid_dates_rejected_before_sql(self):
        for changes in [
            {"end_date": "2026-08-31"}, {"start_date": "esta semana"},
            {"start_date": "2026-02-30"}, {"start_date": 1788220800},
            {"start_date": "2026-09-01T00:00:00"}, {"end_date": "9999-12-31"},
        ]:
            with self.subTest(changes=changes):
                for endpoint in ["/review-vehicles-period", "/evaluate-vehicle-period"]:
                    payload = {**self.period, **changes}
                    if endpoint == "/evaluate-vehicle-period":
                        payload["matricula"] = "0001ABC"
                    response = await self.client.post(endpoint, json=payload)
                    self.assertEqual(response.status_code, 422)
        self.repository.load_operational_rows_between.assert_not_called()

    async def test_same_day_is_valid_and_includes_whole_day(self):
        response = await self.client.post("/review-vehicles-period", json={"start_date": "2026-09-07", "end_date": "2026-09-07"})
        self.assertEqual(response.status_code, 200)
        self.repository.load_operational_rows_between.assert_called_once_with(
            datetime(2026, 9, 7), datetime(2026, 9, 8), matricula=None, limit=1001
        )

    async def test_empty_plate_and_extra_fields_rejected(self):
        for changes in [{"matricula": " "}, {"matricula": "X" * 33}, {"sql": "SELECT 1"}]:
            response = await self.client.post("/evaluate-vehicle-period", json={**self.period, "matricula": "0001ABC", **changes})
            self.assertEqual(response.status_code, 422)
        self.repository.load_operational_rows_between.assert_not_called()

    async def test_over_limit_rejected_without_evaluating_partial_data(self):
        self.repository.load_operational_rows_between.return_value = [trip("R")] * (MAX_PERIOD_TRIPS + 1)
        for endpoint in ["/review-vehicles-period", "/evaluate-vehicle-period"]:
            payload = dict(self.period)
            if endpoint == "/evaluate-vehicle-period":
                payload["matricula"] = "0001ABC"
            response = await self.client.post(endpoint, json=payload)
            self.assertEqual(response.status_code, 413)
            self.assertNotIn("results", response.json())

    async def test_exact_limit_accepted(self):
        self.repository.load_operational_rows_between.return_value = [trip("N")] * MAX_PERIOD_TRIPS
        response = await self.client.post("/review-vehicles-period", json=self.period)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_trips"], MAX_PERIOD_TRIPS)

    async def test_sql_required(self):
        for source, repository in [("csv", self.repository), ("sql", None)]:
            self.app.state.data_source = source
            self.app.state.trip_repository = repository
            for endpoint in ["/review-vehicles-period", "/evaluate-vehicle-period"]:
                payload = dict(self.period)
                if endpoint == "/evaluate-vehicle-period":
                    payload["matricula"] = "0001ABC"
                response = await self.client.post(endpoint, json=payload)
                self.assertEqual(response.status_code, 503)

    async def test_unknown_plate_review_is_explicit(self):
        self.repository.load_operational_rows_between.return_value = [trip("R", None, consumption=400)]
        response = await self.client.post("/review-vehicles-period", json=self.period)
        self.assertEqual(response.json()["vehicles"], [])
        self.assertEqual(response.json()["excluded_review_trips"], 1)
        self.assertEqual(response.json()["excluded_review_identifiers"], 1)
