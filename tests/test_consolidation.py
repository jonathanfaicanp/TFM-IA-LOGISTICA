import unittest

from src.consolidation import AnalysisCoverage, consolidate_results
from src.models import DetectionResult, DetectionStatus, TemporalDetectionResult


def consumption_result(status):
    return DetectionResult(
        codigo_viaje="T1", codigo_vehiculo="V1", fecha="2026-01-01 00:00:00",
        status=status, reason="synthetic", distancia_km=2.0, consumo_litros=.2,
        consumo_l_100km=10.0, baseline=10.0, relative_deviation=0.0, mad=1.0,
        robust_z=0.0, baseline_type="contextual", historical_observations=100,
        distance_range="> 1 y <= 2",
    )


def temporal_result(status):
    return TemporalDetectionResult(
        codigo_viaje="T1", codigo_vehiculo="V1", fecha="2026-01-01 00:00:00",
        status=status, reason="synthetic", distancia_km=2.0, duration_minutes=6.0,
        minutes_per_km=3.0, baseline=3.0, relative_deviation=0.0, mad=.5,
        robust_z=0.0, baseline_type="contextual", historical_observations=100,
        distance_range="> 1 y <= 2",
    )


class ConsolidationTests(unittest.TestCase):
    def test_confirmed_status_combinations(self):
        normal = DetectionStatus.NO_RELEVANT_DEVIATION
        review = DetectionStatus.REVIEW
        unavailable = DetectionStatus.NOT_EVALUABLE
        cases = (
            (normal, normal, normal, AnalysisCoverage.COMPLETE, []),
            (review, normal, review, AnalysisCoverage.COMPLETE, ["consumption"]),
            (normal, review, review, AnalysisCoverage.COMPLETE, ["temporal"]),
            (review, review, review, AnalysisCoverage.COMPLETE, ["consumption", "temporal"]),
            (unavailable, normal, normal, AnalysisCoverage.PARTIAL, []),
            (unavailable, review, review, AnalysisCoverage.PARTIAL, ["temporal"]),
            (unavailable, unavailable, unavailable, AnalysisCoverage.NONE, []),
        )
        for consumption, temporal, overall, coverage, signals in cases:
            with self.subTest(consumption=consumption, temporal=temporal):
                result = consolidate_results(consumption_result(consumption), temporal_result(temporal))
                self.assertEqual(result.overall_status, overall)
                self.assertEqual(result.analysis_coverage, coverage)
                self.assertEqual(result.review_signals, signals)

    def test_serialization_keeps_original_signal_results(self):
        result = consolidate_results(consumption_result(DetectionStatus.REVIEW), temporal_result(DetectionStatus.NOT_EVALUABLE)).to_dict()
        self.assertEqual(result["overall_status"], "REVIEW")
        self.assertEqual(result["analysis_coverage"], "PARTIAL")
        self.assertEqual(result["signals"]["consumption"]["status"], "REVIEW")
        self.assertEqual(result["signals"]["temporal"]["status"], "NOT_EVALUABLE")

    def test_missing_consumption_does_not_prevent_temporal_consolidation(self):
        consumption = consumption_result(DetectionStatus.NOT_EVALUABLE)
        consumption = DetectionResult(
            **{
                **consumption.__dict__,
                "reason": "MISSING_CONSUMPTION",
                "consumo_litros": None,
                "consumo_l_100km": None,
                "baseline": None,
                "relative_deviation": None,
                "mad": None,
                "robust_z": None,
                "baseline_type": None,
                "historical_observations": None,
            }
        )

        result = consolidate_results(
            consumption, temporal_result(DetectionStatus.NO_RELEVANT_DEVIATION)
        )

        self.assertEqual(result.overall_status, DetectionStatus.NO_RELEVANT_DEVIATION)
        self.assertEqual(result.analysis_coverage, AnalysisCoverage.PARTIAL)
        self.assertEqual(
            result.signals["consumption"]["reason"], "MISSING_CONSUMPTION"
        )
        self.assertEqual(
            result.signals["temporal"]["status"], "NO_RELEVANT_DEVIATION"
        )

    def test_different_trip_results_are_rejected(self):
        temporal = temporal_result(DetectionStatus.REVIEW)
        temporal = TemporalDetectionResult(**{**temporal.__dict__, "codigo_viaje": "T2"})
        with self.assertRaisesRegex(ValueError, "same trip_id"):
            consolidate_results(consumption_result(DetectionStatus.REVIEW), temporal)


if __name__ == "__main__":
    unittest.main()
