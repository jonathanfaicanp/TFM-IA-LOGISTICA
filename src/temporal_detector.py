"""Reusable temporal deviation detector v1 for trips over one kilometre."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping

from .baseline import (
    HISTORICAL_YEARS,
    MAD_SCALE,
    MINIMUM_CONTEXT_OBSERVATIONS,
    MINIMUM_VEHICLE_OBSERVATIONS,
    BaselineRepository,
    median_mad,
    robust_z,
)
from .data_processing import normalize_temporal_trip
from .detector import EVALUATION_YEAR, classify
from .models import BaselineStats, DetectionStatus, NormalizedTemporalTrip, TemporalDetectionResult


def _stats(values: list[float], baseline_type: str) -> BaselineStats:
    centre, mad = median_mad(values)
    return BaselineStats(centre, mad, MAD_SCALE * mad, baseline_type, len(values))


def build_temporal_baselines(records: Iterable[NormalizedTemporalTrip]) -> BaselineRepository:
    by_vehicle: dict[str, list[float]] = defaultdict(list)
    by_context: dict[tuple[str, str], list[float]] = defaultdict(list)
    for record in records:
        if record.year not in HISTORICAL_YEARS or record.validation_reason is not None:
            continue
        if record.minutes_per_km is None or record.distance_range is None:
            continue
        by_vehicle[record.codigo_vehiculo].append(record.minutes_per_km)
        by_context[(record.codigo_vehiculo, record.distance_range)].append(record.minutes_per_km)

    eligible = {vehicle for vehicle, values in by_vehicle.items() if len(values) >= MINIMUM_VEHICLE_OBSERVATIONS}
    vehicles = {vehicle: _stats(by_vehicle[vehicle], "vehicle_fallback") for vehicle in eligible}
    contexts = {
        key: _stats(values, "contextual")
        for key, values in by_context.items()
        if key[0] in eligible and len(values) >= MINIMUM_CONTEXT_OBSERVATIONS
    }
    return BaselineRepository(vehicles, contexts)


class TemporalDetectorV1:
    """Classify upper-tail deviations in minutes/km without inferring causes."""

    def __init__(self, baselines: BaselineRepository):
        self.baselines = baselines

    @classmethod
    def from_history(cls, rows: Iterable[Mapping[str, object]]) -> "TemporalDetectorV1":
        return cls(build_temporal_baselines(normalize_temporal_trip(row) for row in rows))

    def evaluate(self, row: Mapping[str, object]) -> TemporalDetectionResult:
        return self.evaluate_normalized(normalize_temporal_trip(row))

    def evaluate_normalized(self, trip: NormalizedTemporalTrip) -> TemporalDetectionResult:
        if trip.year != EVALUATION_YEAR:
            return self._result(trip, DetectionStatus.NOT_EVALUABLE, "OUTSIDE_EVALUATION_PERIOD")
        if trip.validation_reason is not None:
            return self._result(trip, DetectionStatus.NOT_EVALUABLE, trip.validation_reason)
        scope = self.baselines.select(trip)
        if scope is None:
            return self._result(trip, DetectionStatus.NOT_EVALUABLE, "NO_HISTORICAL_BASELINE")
        if scope.mad == 0:
            return self._result(
                trip,
                DetectionStatus.NOT_EVALUABLE,
                "ZERO_HISTORICAL_MAD",
                baseline=scope.baseline,
                mad=scope.mad,
                baseline_type=scope.baseline_type,
                historical_observations=scope.historical_observations,
            )
        relative = (trip.minutes_per_km - scope.baseline) / scope.baseline
        score = robust_z(trip.minutes_per_km, scope.baseline, scope.mad)
        status = classify(relative, score)
        reason = "TEMPORAL_V1_THRESHOLDS_EXCEEDED" if status is DetectionStatus.REVIEW else "TEMPORAL_V1_THRESHOLDS_NOT_BOTH_EXCEEDED"
        return self._result(
            trip,
            status,
            reason,
            baseline=scope.baseline,
            relative_deviation=relative,
            mad=scope.mad,
            robust_z=score,
            baseline_type=scope.baseline_type,
            historical_observations=scope.historical_observations,
        )

    @staticmethod
    def _result(trip: NormalizedTemporalTrip, status: DetectionStatus, reason: str, **metrics) -> TemporalDetectionResult:
        return TemporalDetectionResult(
            codigo_viaje=trip.codigo_viaje,
            codigo_vehiculo=trip.codigo_vehiculo,
            fecha=trip.fecha,
            status=status,
            reason=reason,
            distancia_km=trip.distancia_km,
            duration_minutes=trip.duration_minutes,
            minutes_per_km=trip.minutes_per_km,
            baseline=metrics.get("baseline"),
            relative_deviation=metrics.get("relative_deviation"),
            mad=metrics.get("mad"),
            robust_z=metrics.get("robust_z"),
            baseline_type=metrics.get("baseline_type"),
            historical_observations=metrics.get("historical_observations"),
            distance_range=trip.distance_range,
        )
