"""Parsing and unit normalization for consumption and temporal signals."""

from __future__ import annotations

from datetime import datetime
from typing import Mapping

from .models import NormalizedTemporalTrip, NormalizedTrip


DISTANCE_RANGES = (
    "<= 1",
    "> 1 y <= 2",
    "> 2 y <= 5",
    "> 5 y <= 10",
    "> 10 y <= 20",
    "> 20 y <= 50",
    "> 50 y <= 100",
    "> 100 y <= 300",
    "> 300",
)


def parse_number(value: str | int | float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = value.strip().replace("\u00a0", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    return float(text)


def distance_range(distance_km: float) -> str:
    for upper, label in zip((1, 2, 5, 10, 20, 50, 100, 300), DISTANCE_RANGES):
        if distance_km <= upper:
            return label
    return DISTANCE_RANGES[-1]


def normalize_trip(row: Mapping[str, object]) -> NormalizedTrip:
    start = datetime.fromisoformat(str(row["Fecha de inicio"]).strip())
    distance_km = parse_number(row["Distancia"]) / 1000
    consumption_liters = parse_number(row["Consumo"]) / 1000
    common = {
        "codigo_viaje": str(row["Codigo Viaje"]) if row.get("Codigo Viaje") is not None else None,
        "codigo_vehiculo": str(row["Codigo Vehiculo"]),
        "fecha": start.isoformat(sep=" "),
        "year": start.year,
        "distancia_km": distance_km,
        "consumo_litros": consumption_liters,
    }
    if consumption_liters <= 0:
        return NormalizedTrip(**common, consumo_l_100km=None, distance_range=None, validation_reason="NON_POSITIVE_CONSUMPTION")
    if distance_km <= 0:
        return NormalizedTrip(**common, consumo_l_100km=None, distance_range=None, validation_reason="NON_POSITIVE_DISTANCE")
    return NormalizedTrip(
        **common,
        consumo_l_100km=consumption_liters / distance_km * 100,
        distance_range=distance_range(distance_km),
    )


def normalize_temporal_trip(row: Mapping[str, object]) -> NormalizedTemporalTrip:
    start = datetime.fromisoformat(str(row["Fecha de inicio"]).strip())
    distance_km = parse_number(row["Distancia"]) / 1000
    duration_minutes = parse_number(row["Duracion"]) / 60
    common = {
        "codigo_viaje": str(row["Codigo Viaje"]) if row.get("Codigo Viaje") is not None else None,
        "codigo_vehiculo": str(row["Codigo Vehiculo"]),
        "fecha": start.isoformat(sep=" "),
        "year": start.year,
        "distancia_km": distance_km,
        "duration_minutes": duration_minutes,
    }
    if duration_minutes <= 0:
        return NormalizedTemporalTrip(**common, minutes_per_km=None, distance_range=None, validation_reason="NON_POSITIVE_DURATION")
    if distance_km <= 0:
        return NormalizedTemporalTrip(**common, minutes_per_km=None, distance_range=None, validation_reason="NON_POSITIVE_DISTANCE")
    if distance_km <= 1:
        return NormalizedTemporalTrip(
            **common,
            minutes_per_km=duration_minutes / distance_km,
            distance_range=distance_range(distance_km),
            validation_reason="DISTANCE_NOT_ABOVE_1_KM",
        )
    return NormalizedTemporalTrip(
        **common,
        minutes_per_km=duration_minutes / distance_km,
        distance_range=distance_range(distance_km),
    )
