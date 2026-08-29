"""Reusable consumption deviation detector v1."""

from .baseline import BaselineRepository, build_baselines
from .data_processing import normalize_trip
from .detector import DetectorV1
from .models import DetectionResult, DetectionStatus, NormalizedTrip

__all__ = [
    "BaselineRepository",
    "DetectionResult",
    "DetectionStatus",
    "DetectorV1",
    "NormalizedTrip",
    "build_baselines",
    "normalize_trip",
]
