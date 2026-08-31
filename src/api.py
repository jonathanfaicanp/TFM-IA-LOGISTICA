"""Minimal HTTP boundary for the reusable analytical layer."""

from __future__ import annotations

import os
from collections.abc import Mapping
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from pydantic import BaseModel, ConfigDict

from .analytical_service import AnalyticalService
from .consolidation import AnalysisCoverage
from .models import DetectionStatus
from .sql_repository import SqlHistoricalRepository


DEFAULT_DATA_PATH = Path("data/datos_operativa.csv")
DATA_PATH_ENVIRONMENT_VARIABLE = "TFM_DATA_PATH"
DATA_SOURCE_ENVIRONMENT_VARIABLE = "TFM_DATA_SOURCE"


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


class HealthResponse(BaseModel):
    status: str


class ConsolidatedResponse(BaseModel):
    trip_id: str | None
    vehicle_id: str
    timestamp: str
    distance_km: float
    overall_status: DetectionStatus
    analysis_coverage: AnalysisCoverage
    review_signals: list[str]
    signals: dict[str, dict]


def create_app(service: AnalyticalService | None = None, historical_path: Path | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        if service is not None:
            application.state.analytical_service = service
        else:
            if historical_path is not None:
                application.state.analytical_service = AnalyticalService.from_csv(historical_path)
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

    return application


app = create_app()
