"""Consolidate independent analytical signals for the same trip."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from .models import DetectionResult, DetectionStatus, TemporalDetectionResult


class AnalysisCoverage(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    NONE = "NONE"


@dataclass(frozen=True)
class ConsolidatedResult:
    trip_id: str | None
    vehicle_id: str
    timestamp: str
    distance_km: float
    overall_status: DetectionStatus
    analysis_coverage: AnalysisCoverage
    review_signals: list[str]
    signals: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["overall_status"] = self.overall_status.value
        result["analysis_coverage"] = self.analysis_coverage.value
        return result


def consolidate_results(consumption: DetectionResult, temporal: TemporalDetectionResult) -> ConsolidatedResult:
    """Combine two detector results without changing either signal."""
    identity_fields = (
        (consumption.codigo_viaje, temporal.codigo_viaje, "trip_id"),
        (consumption.codigo_vehiculo, temporal.codigo_vehiculo, "vehicle_id"),
        (consumption.fecha, temporal.fecha, "timestamp"),
        (consumption.distancia_km, temporal.distancia_km, "distance_km"),
    )
    for first, second, label in identity_fields:
        if first != second:
            raise ValueError(f"Signal results do not refer to the same {label}")

    statuses = {"consumption": consumption.status, "temporal": temporal.status}
    review_signals = [name for name, status in statuses.items() if status is DetectionStatus.REVIEW]
    not_evaluable = sum(status is DetectionStatus.NOT_EVALUABLE for status in statuses.values())
    coverage = AnalysisCoverage.NONE if not_evaluable == 2 else AnalysisCoverage.PARTIAL if not_evaluable == 1 else AnalysisCoverage.COMPLETE
    if review_signals:
        overall = DetectionStatus.REVIEW
    elif not_evaluable < 2:
        overall = DetectionStatus.NO_RELEVANT_DEVIATION
    else:
        overall = DetectionStatus.NOT_EVALUABLE

    return ConsolidatedResult(
        trip_id=consumption.codigo_viaje,
        vehicle_id=consumption.codigo_vehiculo,
        timestamp=consumption.fecha,
        distance_km=consumption.distancia_km,
        overall_status=overall,
        analysis_coverage=coverage,
        review_signals=review_signals,
        signals={"consumption": consumption.to_dict(), "temporal": temporal.to_dict()},
    )
