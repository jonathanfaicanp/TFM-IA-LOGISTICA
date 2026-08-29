import json
import unittest

from src.baseline import BaselineRepository
from src.detector import DetectorV1, classify
from src.models import BaselineStats, DetectionStatus
from src.temporal_detector import TemporalDetectorV1


def temporal_row(value=3.0, distance=1500, year=2024, vehicle="1", trip="T1"):
    duration_seconds = value * (distance / 1000) * 60
    return {
        "Codigo Viaje": trip,
        "Codigo Vehiculo": vehicle,
        "Fecha de inicio": f"{year}-01-01",
        "Duracion": duration_seconds,
        "Distancia": distance,
    }


def consumption_row(consumption=100, year=2024):
    return {
        "Codigo Viaje": "C1",
        "Codigo Vehiculo": "1",
        "Fecha de inicio": f"{year}-01-01",
        "Consumo": consumption,
        "Distancia": 1000,
    }


def detector_with_vehicle_baseline(baseline=10.0, mad=1.0):
    stats = BaselineStats(baseline, mad, 1.4826 * mad, "vehicle_fallback", 100)
    return TemporalDetectorV1(BaselineRepository({"1": stats}, {}))


class TemporalDetectorV1Tests(unittest.TestCase):
    def test_distance_at_or_below_one_km_is_not_evaluable(self):
        detector = detector_with_vehicle_baseline()
        for distance in (1000, 500):
            result = detector.evaluate(temporal_row(distance=distance, year=2026))
            self.assertEqual((result.status, result.reason), (DetectionStatus.NOT_EVALUABLE, "DISTANCE_NOT_ABOVE_1_KM"))

    def test_non_positive_duration_is_not_evaluable(self):
        source = temporal_row(year=2026)
        source["Duracion"] = 0
        result = detector_with_vehicle_baseline().evaluate(source)
        self.assertEqual((result.status, result.reason), (DetectionStatus.NOT_EVALUABLE, "NON_POSITIVE_DURATION"))

    def test_vehicle_without_sufficient_history_is_not_evaluable(self):
        detector = TemporalDetectorV1.from_history([temporal_row(value=1 + index / 100) for index in range(99)])
        result = detector.evaluate(temporal_row(year=2026))
        self.assertEqual((result.status, result.reason), (DetectionStatus.NOT_EVALUABLE, "NO_HISTORICAL_BASELINE"))

    def test_contextual_baseline_at_30_observations(self):
        context = [temporal_row(value=1 + index / 100, distance=1500) for index in range(30)]
        remainder = [temporal_row(value=2 + index / 100, distance=3000) for index in range(70)]
        result = TemporalDetectorV1.from_history(context + remainder).evaluate(temporal_row(value=2, distance=1500, year=2026))
        self.assertEqual((result.baseline_type, result.historical_observations), ("contextual", 30))

    def test_vehicle_fallback_when_context_is_below_30(self):
        first = [temporal_row(value=1 + index / 100, distance=1500) for index in range(29)]
        remainder = [temporal_row(value=2 + index / 100, distance=3000) for index in range(71)]
        result = TemporalDetectorV1.from_history(first + remainder).evaluate(temporal_row(value=2, distance=1500, year=2026))
        self.assertEqual((result.baseline_type, result.historical_observations), ("vehicle_fallback", 100))

    def test_review_requires_both_conditions(self):
        result = detector_with_vehicle_baseline(10, 1).evaluate(temporal_row(value=16, distance=3000, year=2026))
        self.assertEqual(result.status, DetectionStatus.REVIEW)
        json.dumps(result.to_dict())

    def test_no_review_when_only_one_condition_holds(self):
        relative_only = detector_with_vehicle_baseline(10, 10).evaluate(temporal_row(value=16, distance=3000, year=2026))
        z_only = detector_with_vehicle_baseline(10, .05).evaluate(temporal_row(value=10.2, distance=3000, year=2026))
        self.assertEqual(relative_only.status, DetectionStatus.NO_RELEVANT_DEVIATION)
        self.assertEqual(z_only.status, DetectionStatus.NO_RELEVANT_DEVIATION)

    def test_threshold_limits_are_strict(self):
        self.assertEqual(classify(.50, 3), DetectionStatus.NO_RELEVANT_DEVIATION)
        self.assertEqual(classify(.60, 2), DetectionStatus.NO_RELEVANT_DEVIATION)

    def test_zero_mad_is_explicitly_not_evaluable(self):
        result = detector_with_vehicle_baseline(10, 0).evaluate(temporal_row(value=12, distance=3000, year=2026))
        self.assertEqual((result.status, result.reason), (DetectionStatus.NOT_EVALUABLE, "ZERO_HISTORICAL_MAD"))

    def test_consumption_detector_regression(self):
        history = [consumption_row(value) for value in ([80, 90, 100, 110, 120] * 20)]
        result = DetectorV1.from_history(history).evaluate(consumption_row(200, 2026))
        self.assertEqual(result.status, DetectionStatus.REVIEW)


if __name__ == "__main__":
    unittest.main()
