"""Small data structures used by the detector v1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class DetectionStatus(str, Enum):
    NOT_EVALUABLE = "NOT_EVALUABLE"
    NO_RELEVANT_DEVIATION = "NO_RELEVANT_DEVIATION"
    REVIEW = "REVIEW"


@dataclass(frozen=True)
class NormalizedTrip:
    codigo_viaje: str | None
    codigo_vehiculo: str
    fecha: str
    year: int
    distancia_km: float | None
    consumo_litros: float | None
    consumo_l_100km: float | None
    distance_range: str | None
    validation_reason: str | None = None


@dataclass(frozen=True)
class BaselineStats:
    baseline: float
    mad: float
    robust_scale: float
    baseline_type: str
    historical_observations: int


@dataclass(frozen=True)
class DetectionResult:
    codigo_viaje: str | None
    codigo_vehiculo: str
    fecha: str
    status: DetectionStatus
    reason: str
    distancia_km: float | None
    consumo_litros: float | None
    consumo_l_100km: float | None
    baseline: float | None
    relative_deviation: float | None
    mad: float | None
    robust_z: float | None
    baseline_type: str | None
    historical_observations: int | None
    distance_range: str | None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        return result
