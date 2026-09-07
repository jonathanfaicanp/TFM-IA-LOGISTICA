import json
import unittest

from src.baseline import MAD_SCALE, build_baselines, median_mad, robust_z
from src.data_processing import DISTANCE_RANGES, distance_range, normalize_trip
from src.detector import DetectorV1, classify
from src.models import DetectionStatus


def row(vehicle="1", date="2024-01-01", distance=1000, consumption=100, trip="T1"):
    return {"Codigo Viaje": trip, "Codigo Vehiculo": vehicle, "Fecha de inicio": date, "Distancia": distance, "Consumo": consumption}


class DetectorV1Tests(unittest.TestCase):
    def test_unit_transformation(self):
        trip = normalize_trip(row(distance="2.000,0", consumption="500,0"))
        self.assertEqual((trip.distancia_km, trip.consumo_litros, trip.consumo_l_100km), (2.0, .5, 25.0))

    def test_normalization_preserves_missing_consumption(self):
        trip = normalize_trip(row(consumption=None))
        self.assertIsNone(trip.consumo_litros)
        self.assertIsNone(trip.consumo_l_100km)
        self.assertEqual(trip.validation_reason, "MISSING_CONSUMPTION")

    def test_distance_ranges(self):
        values = (.5, 1.5, 3, 7, 15, 30, 75, 200, 301)
        self.assertEqual(tuple(distance_range(value) for value in values), DISTANCE_RANGES)

    def test_blank_consumption_is_missing_and_not_evaluable(self):
        detector = self._detector()
        for consumption in ("", "   ", "\t "):
            with self.subTest(consumption=consumption):
                source = row(date="2026-01-01", consumption=consumption)
                trip = normalize_trip(source)
                self.assertIsNone(trip.consumo_litros)
                self.assertIsNone(trip.consumo_l_100km)
                self.assertEqual(trip.validation_reason, "MISSING_CONSUMPTION")
                result = detector.evaluate(source)
                self.assertEqual(result.status, DetectionStatus.NOT_EVALUABLE)
                self.assertEqual(result.reason, "MISSING_CONSUMPTION")

    def test_numeric_consumption_formats_are_preserved(self):
        for consumption in (1500, 1500.0, "1500", "1500.0", "1500,0", " 1.500,0 "):
            with self.subTest(consumption=consumption):
                trip = normalize_trip(row(distance=2000, consumption=consumption))
                self.assertEqual(trip.consumo_litros, 1.5)
                self.assertEqual(trip.consumo_l_100km, 75.0)
                self.assertIsNone(trip.validation_reason)

    def test_contextual_baseline_at_30_observations(self):
        history = [normalize_trip(row(distance=1000, consumption=90 + index % 3)) for index in range(30)]
        history += [normalize_trip(row(distance=3000, consumption=300 + index)) for index in range(70)]
        selected = build_baselines(history).select(normalize_trip(row(date="2026-01-01")))
        self.assertEqual((selected.baseline_type, selected.historical_observations), ("contextual", 30))

    def test_vehicle_fallback_below_30_context_observations(self):
        history = [normalize_trip(row(distance=1000, consumption=90 + index)) for index in range(29)]
        history += [normalize_trip(row(distance=3000, consumption=300 + index)) for index in range(71)]
        selected = build_baselines(history).select(normalize_trip(row(date="2026-01-01")))
        self.assertEqual((selected.baseline_type, selected.historical_observations), ("vehicle_fallback", 100))

    def test_vehicle_below_100_has_no_baseline(self):
        history = [normalize_trip(row(consumption=100 + index)) for index in range(99)]
        self.assertIsNone(build_baselines(history).select(normalize_trip(row(date="2026-01-01"))))

    def test_mad_and_robust_z(self):
        centre, mad = median_mad([1, 2, 3, 4, 5])
        self.assertEqual((centre, mad), (3, 1))
        self.assertAlmostEqual(robust_z(3 + MAD_SCALE, centre, mad), 1)

    def test_zero_mad_is_not_evaluable(self):
        detector = DetectorV1.from_history([row(consumption=100) for _ in range(100)])
        result = detector.evaluate(row(date="2026-01-01", consumption=200))
        self.assertEqual((result.status, result.reason), (DetectionStatus.NOT_EVALUABLE, "ZERO_HISTORICAL_MAD"))

    def test_review_when_both_conditions_hold(self):
        detector = self._detector()
        result = detector.evaluate(row(date="2026-01-01", consumption=200))
        self.assertEqual(result.status, DetectionStatus.REVIEW)
        json.dumps(result.to_dict())

    def test_no_relevant_deviation_when_both_do_not_hold(self):
        result = self._detector().evaluate(row(date="2026-01-01", consumption=110))
        self.assertEqual(result.status, DetectionStatus.NO_RELEVANT_DEVIATION)

    def test_threshold_comparisons_are_strict(self):
        self.assertEqual(classify(.50, 3), DetectionStatus.NO_RELEVANT_DEVIATION)
        self.assertEqual(classify(.51, 2), DetectionStatus.NO_RELEVANT_DEVIATION)
        self.assertEqual(classify(.51, 2.01), DetectionStatus.REVIEW)

    def test_non_positive_consumption_is_not_evaluable(self):
        result = self._detector().evaluate(row(date="2026-01-01", consumption=0))
        self.assertEqual((result.status, result.reason), (DetectionStatus.NOT_EVALUABLE, "NON_POSITIVE_CONSUMPTION"))

    def test_missing_consumption_is_not_evaluable(self):
        result = self._detector().evaluate(row(date="2026-01-01", consumption=None))
        self.assertEqual(
            (result.status, result.reason),
            (DetectionStatus.NOT_EVALUABLE, "MISSING_CONSUMPTION"),
        )
        self.assertIsNone(result.consumo_litros)
        self.assertIsNone(result.consumo_l_100km)

    def test_non_positive_distance_is_not_evaluable(self):
        result = self._detector().evaluate(row(date="2026-01-01", distance=0))
        self.assertEqual((result.status, result.reason), (DetectionStatus.NOT_EVALUABLE, "NON_POSITIVE_DISTANCE"))

    def test_only_2026_is_evaluated(self):
        result = self._detector().evaluate(row(date="2025-12-31"))
        self.assertEqual((result.status, result.reason), (DetectionStatus.NOT_EVALUABLE, "OUTSIDE_EVALUATION_PERIOD"))

    @staticmethod
    def _detector():
        consumptions = [80, 90, 100, 110, 120] * 20
        return DetectorV1.from_history([row(consumption=value) for value in consumptions])


if __name__ == "__main__":
    unittest.main()
