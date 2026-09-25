"""Minimal HTTP boundary for the reusable analytical layer."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .analytical_service import AnalyticalService
from .consolidation import AnalysisCoverage
from .models import DetectionStatus
from .sql_repository import SqlHistoricalRepository


DEFAULT_DATA_PATH = Path("data/datos_operativa.csv")
DATA_PATH_ENVIRONMENT_VARIABLE = "TFM_DATA_PATH"
DATA_SOURCE_ENVIRONMENT_VARIABLE = "TFM_DATA_SOURCE"
MAX_PERIOD_TRIPS = 1000


def normalize_operational_registration(value: str | None) -> str | None:
    """Recognize only the requested plate format, independently of detection."""
    if value is None:
        return None
    normalized = value.strip().upper()
    return normalized if re.fullmatch(r"[0-9]{4}[A-Z]{3}", normalized) else None


def build_analytical_service(environment: Mapping[str, str] | None = None) -> AnalyticalService:
    values = os.environ if environment is None else environment
    data_source = values.get(DATA_SOURCE_ENVIRONMENT_VARIABLE, "csv").strip().lower()
    if data_source == "csv":
        return AnalyticalService.from_csv(
            Path(values.get(DATA_PATH_ENVIRONMENT_VARIABLE, DEFAULT_DATA_PATH))
        )
    if data_source == "sql":
        rows = SqlHistoricalRepository.from_environment(values).load_historical_rows()
        return AnalyticalService.from_history(rows)
    raise ValueError(
        f"Valor no válido para {DATA_SOURCE_ENVIRONMENT_VARIABLE}: {data_source!r}. "
        "Los valores admitidos son 'csv' y 'sql'."
    )


class EvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trip_id: str
    vehicle_id: str
    timestamp: datetime
    distance_m: float
    consumption_ml: float
    duration_seconds: float

    def to_source_row(self) -> dict[str, object]:
        return {
            "Codigo Viaje": self.trip_id,
            "Codigo Vehiculo": self.vehicle_id,
            "Fecha de inicio": self.timestamp.isoformat(sep=" "),
            "Distancia": self.distance_m,
            "Consumo": self.consumption_ml,
            "Duracion": self.duration_seconds,
        }


class TripEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trip_id: str


class HealthResponse(BaseModel):
    status: str


class PeriodRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: date
    end_date: date

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def explicit_date(cls, value):
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError("Use fechas explícitas YYYY-MM-DD.")
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            raise ValueError("Use fechas explícitas YYYY-MM-DD.") from None
        if parsed.isoformat() != value:
            raise ValueError("Use fechas explícitas YYYY-MM-DD.")
        return parsed

    @model_validator(mode="after")
    def ordered_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date no puede ser anterior a start_date.")
        if self.end_date == date.max:
            raise ValueError("end_date debe ser anterior a 9999-12-31.")
        return self

    def bounds(self) -> tuple[datetime, datetime]:
        return (
            datetime.combine(self.start_date, time.min),
            datetime.combine(self.end_date + timedelta(days=1), time.min),
        )


class VehiclePeriodRequest(PeriodRequest):
    matricula: str = Field(min_length=1, max_length=32)

    @field_validator("matricula")
    @classmethod
    def clean_plate(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("matricula no puede estar vacía.")
        return value


class ConsolidatedResponse(BaseModel):
    trip_id: str | None
    vehicle_id: str
    timestamp: str
    distance_km: float
    overall_status: DetectionStatus
    analysis_coverage: AnalysisCoverage
    review_signals: list[str]
    signals: dict[str, dict]


class PeriodResponse(BaseModel):
    start_date: date
    end_date: date
    total_trips: int
    status_counts: dict[DetectionStatus, int]
    coverage_counts: dict[AnalysisCoverage, int]


class VehiclePeriodResponse(PeriodResponse):
    matricula: str
    results: list[ConsolidatedResponse]


class ReviewVehicleResponse(BaseModel):
    matricula: str | None
    review_count: int
    trip_ids: list[str | None]


class ReviewPeriodResponse(PeriodResponse):
    vehicles: list[ReviewVehicleResponse]
    excluded_review_trips: int = 0
    excluded_review_identifiers: int = 0


def evaluate_period(payload: PeriodRequest, request: Request, matricula: str | None = None):
    repository = request.app.state.trip_repository
    if request.app.state.data_source != "sql" or repository is None:
        raise HTTPException(status_code=503, detail="La consulta por periodo requiere acceso operacional SQL.")
    start, end = payload.bounds()
    rows = repository.load_operational_rows_between(
        start, end, matricula=matricula, limit=MAX_PERIOD_TRIPS + 1
    )
    if len(rows) > MAX_PERIOD_TRIPS:
        raise HTTPException(status_code=413, detail="El periodo supera 1000 viajes; reduzca el rango de fechas.")
    results = [request.app.state.analytical_service.evaluate(row).to_dict() for row in rows]
    summary = {
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "total_trips": len(results),
        "status_counts": {status.value: sum(r["overall_status"] == status.value for r in results) for status in DetectionStatus},
        "coverage_counts": {coverage.value: sum(r["analysis_coverage"] == coverage.value for r in results) for coverage in AnalysisCoverage},
    }
    return rows, results, summary


def create_app(
    service: AnalyticalService | None = None,
    historical_path: Path | None = None,
    repository: SqlHistoricalRepository | None = None,
    data_source: str | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        configured_source = (
            data_source
            or ("sql" if repository is not None else os.environ.get(DATA_SOURCE_ENVIRONMENT_VARIABLE, "csv"))
        ).strip().lower()
        application.state.data_source = configured_source
        application.state.trip_repository = repository
        if service is not None:
            application.state.analytical_service = service
        else:
            if historical_path is not None:
                application.state.analytical_service = AnalyticalService.from_csv(historical_path)
            elif configured_source == "sql":
                sql_repository = repository or SqlHistoricalRepository.from_environment()
                application.state.trip_repository = sql_repository
                application.state.analytical_service = AnalyticalService.from_history(
                    sql_repository.load_historical_rows()
                )
            else:
                application.state.analytical_service = build_analytical_service()
        yield

    application = FastAPI(title="TFM Analytical Layer", version="1.0.0", lifespan=lifespan)

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @application.post("/evaluate", response_model=ConsolidatedResponse)
    def evaluate(payload: EvaluationRequest, request: Request) -> dict:
        result = request.app.state.analytical_service.evaluate(payload.to_source_row())
        return result.to_dict()

    @application.post("/evaluate-trip", response_model=ConsolidatedResponse)
    def evaluate_trip(payload: TripEvaluationRequest, request: Request) -> dict:
        if request.app.state.data_source != "sql":
            raise HTTPException(
                status_code=503,
                detail="/evaluate-trip requiere acceso operacional SQL (TFM_DATA_SOURCE=sql).",
            )
        if request.app.state.trip_repository is None:
            raise HTTPException(
                status_code=503,
                detail="El repositorio operacional SQL no está configurado.",
            )
        trip = request.app.state.trip_repository.get_trip_by_id(payload.trip_id)
        if trip is None:
            raise HTTPException(
                status_code=404,
                detail=f"No existe el viaje con trip_id {payload.trip_id!r}.",
            )
        result = request.app.state.analytical_service.evaluate(trip)
        return result.to_dict()

    @application.post("/evaluate-vehicle-period", response_model=VehiclePeriodResponse)
    def evaluate_vehicle_period(payload: VehiclePeriodRequest, request: Request) -> dict:
        _, results, summary = evaluate_period(payload, request, payload.matricula)
        return {**summary, "matricula": payload.matricula, "results": results}

    @application.post("/review-vehicles-period", response_model=ReviewPeriodResponse)
    def review_vehicles_period(payload: PeriodRequest, request: Request) -> dict:
        rows, results, summary = evaluate_period(payload, request)
        groups = {}
        excluded_trips = 0
        excluded_identifiers = set()
        for row, result in zip(rows, results):
            if result["overall_status"] != DetectionStatus.REVIEW.value:
                continue
            identifier = row.get("matricula")
            plate = normalize_operational_registration(identifier)
            if plate is None:
                excluded_trips += 1
                excluded_identifiers.add(identifier.strip().upper() if identifier is not None else None)
                continue
            group = groups.setdefault(plate, {"matricula": plate, "review_count": 0, "trip_ids": []})
            group["review_count"] += 1
            group["trip_ids"].append(result["trip_id"])
        return {
            **summary,
            "vehicles": sorted(groups.values(), key=lambda group: group["matricula"]),
            "excluded_review_trips": excluded_trips,
            "excluded_review_identifiers": len(excluded_identifiers),
        }

    return application


app = create_app()
