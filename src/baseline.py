"""Historical B30 baseline construction for the detector v1."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import median
from typing import Iterable

from .models import BaselineStats, NormalizedTrip


HISTORICAL_YEARS = (2024, 2025)
MINIMUM_VEHICLE_OBSERVATIONS = 100
MINIMUM_CONTEXT_OBSERVATIONS = 30
MAD_SCALE = 1.4826


def median_mad(values: Iterable[float]) -> tuple[float, float]:
    sample = list(values)
    centre = median(sample)
    return centre, median(abs(value - centre) for value in sample)


def robust_z(value: float, centre: float, mad: float) -> float | None:
    return None if mad == 0 else (value - centre) / (MAD_SCALE * mad)


@dataclass(frozen=True)
class BaselineRepository:
    vehicles: dict[str, BaselineStats]
    contexts: dict[tuple[str, str], BaselineStats]

    def select(self, trip: NormalizedTrip) -> BaselineStats | None:
        contextual = self.contexts.get((trip.codigo_vehiculo, trip.distance_range or ""))
        return contextual if contextual is not None else self.vehicles.get(trip.codigo_vehiculo)


def _stats(values: list[float], baseline_type: str) -> BaselineStats:
    centre, mad = median_mad(values)
    return BaselineStats(centre, mad, MAD_SCALE * mad, baseline_type, len(values))


def build_baselines(records: Iterable[NormalizedTrip]) -> BaselineRepository:
    by_vehicle: dict[str, list[float]] = defaultdict(list)
    by_context: dict[tuple[str, str], list[float]] = defaultdict(list)
    for record in records:
        if record.year not in HISTORICAL_YEARS or record.validation_reason is not None:
            continue
        value = record.consumo_l_100km
        if value is None or record.distance_range is None:
            continue
        by_vehicle[record.codigo_vehiculo].append(value)
        by_context[(record.codigo_vehiculo, record.distance_range)].append(value)

    eligible = {vehicle for vehicle, values in by_vehicle.items() if len(values) >= MINIMUM_VEHICLE_OBSERVATIONS}
    vehicles = {vehicle: _stats(by_vehicle[vehicle], "vehicle_fallback") for vehicle in eligible}
    contexts = {
        key: _stats(values, "contextual")
        for key, values in by_context.items()
        if key[0] in eligible and len(values) >= MINIMUM_CONTEXT_OBSERVATIONS
    }
    return BaselineRepository(vehicles, contexts)
