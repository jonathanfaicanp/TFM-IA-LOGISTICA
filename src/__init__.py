"""Reusable consumption deviation detector v1."""

from .baseline import BaselineRepository, build_baselines
from .data_processing import normalize_temporal_trip, normalize_trip
from .detector import DetectorV1
from .models import DetectionResult, DetectionStatus, NormalizedTemporalTrip, NormalizedTrip, TemporalDetectionResult
from .temporal_detector import TemporalDetectorV1, build_temporal_baselines

__all__ = [
    "BaselineRepository",
    "DetectionResult",
    "DetectionStatus",
    "DetectorV1",
    "NormalizedTrip",
    "NormalizedTemporalTrip",
    "TemporalDetectionResult",
    "TemporalDetectorV1",
    "build_baselines",
    "build_temporal_baselines",
    "normalize_temporal_trip",
    "normalize_trip",
]
