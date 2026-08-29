"""Reusable consumption deviation detector v1."""

from .baseline import BaselineRepository, build_baselines
from .analytical_service import AnalyticalService
from .consolidation import AnalysisCoverage, ConsolidatedResult, consolidate_results
from .data_processing import normalize_temporal_trip, normalize_trip
from .detector import DetectorV1
from .models import DetectionResult, DetectionStatus, NormalizedTemporalTrip, NormalizedTrip, TemporalDetectionResult
from .temporal_detector import TemporalDetectorV1, build_temporal_baselines

__all__ = [
    "BaselineRepository",
    "AnalyticalService",
    "AnalysisCoverage",
    "ConsolidatedResult",
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
    "consolidate_results",
]
