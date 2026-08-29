"""Application service joining detector initialization and consolidation."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from pathlib import Path

from .consolidation import ConsolidatedResult, consolidate_results
from .detector import DetectorV1
from .temporal_detector import TemporalDetectorV1


class AnalyticalService:
    def __init__(self, consumption_detector: DetectorV1, temporal_detector: TemporalDetectorV1):
        self.consumption_detector = consumption_detector
        self.temporal_detector = temporal_detector

    @classmethod
    def from_history(cls, rows: Iterable[Mapping[str, object]]) -> "AnalyticalService":
        history = list(rows)
        return cls(DetectorV1.from_history(history), TemporalDetectorV1.from_history(history))

    @classmethod
    def from_csv(cls, path: Path) -> "AnalyticalService":
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            return cls.from_history(csv.DictReader(file, delimiter=";"))

    def evaluate(self, row: Mapping[str, object]) -> ConsolidatedResult:
        consumption = self.consumption_detector.evaluate(row)
        temporal = self.temporal_detector.evaluate(row)
        return consolidate_results(consumption, temporal)
