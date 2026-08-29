"""Classification rule for consumption deviation detector v1."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .baseline import BaselineRepository, build_baselines, robust_z
from .data_processing import normalize_trip
from .models import DetectionResult, DetectionStatus, NormalizedTrip


EVALUATION_YEAR = 2026


def classify(relative_deviation: float, score: float) -> DetectionStatus:
    if relative_deviation > 0.50 and score > 2:
        return DetectionStatus.REVIEW
    return DetectionStatus.NO_RELEVANT_DEVIATION


class DetectorV1:
    def __init__(self, baselines: BaselineRepository):
        self.baselines = baselines

    @classmethod
    def from_history(cls, rows: Iterable[Mapping[str, object]]) -> "DetectorV1":
        return cls(build_baselines(normalize_trip(row) for row in rows))

    def evaluate(self, row: Mapping[str, object]) -> DetectionResult:
        return self.evaluate_normalized(normalize_trip(row))

    def evaluate_normalized(self, trip: NormalizedTrip) -> DetectionResult:
        if trip.year != EVALUATION_YEAR:
            return self._result(trip, DetectionStatus.NOT_EVALUABLE, "OUTSIDE_EVALUATION_PERIOD")
        if trip.validation_reason is not None:
            return self._result(trip, DetectionStatus.NOT_EVALUABLE, trip.validation_reason)
        scope = self.baselines.select(trip)
        if scope is None:
            return self._result(trip, DetectionStatus.NOT_EVALUABLE, "NO_HISTORICAL_BASELINE")
        if scope.mad == 0:
            return self._result(
                trip, DetectionStatus.NOT_EVALUABLE, "ZERO_HISTORICAL_MAD",
                baseline=scope.baseline, mad=scope.mad, baseline_type=scope.baseline_type,
                historical_observations=scope.historical_observations,
            )
        relative = (trip.consumo_l_100km - scope.baseline) / scope.baseline
        score = robust_z(trip.consumo_l_100km, scope.baseline, scope.mad)
        status = classify(relative, score)
        reason = "V1_THRESHOLDS_EXCEEDED" if status is DetectionStatus.REVIEW else "V1_THRESHOLDS_NOT_BOTH_EXCEEDED"
        return self._result(
            trip, status, reason, baseline=scope.baseline, relative_deviation=relative,
            mad=scope.mad, robust_z=score, baseline_type=scope.baseline_type,
            historical_observations=scope.historical_observations,
        )

    @staticmethod
    def _result(trip: NormalizedTrip, status: DetectionStatus, reason: str, **metrics) -> DetectionResult:
        return DetectionResult(
            codigo_viaje=trip.codigo_viaje, codigo_vehiculo=trip.codigo_vehiculo,
            fecha=trip.fecha, status=status, reason=reason,
            distancia_km=trip.distancia_km, consumo_litros=trip.consumo_litros,
            consumo_l_100km=trip.consumo_l_100km, distance_range=trip.distance_range,
            baseline=metrics.get("baseline"), relative_deviation=metrics.get("relative_deviation"),
            mad=metrics.get("mad"), robust_z=metrics.get("robust_z"),
            baseline_type=metrics.get("baseline_type"), historical_observations=metrics.get("historical_observations"),
        )
