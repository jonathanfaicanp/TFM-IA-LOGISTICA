import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from evaluation.conversational_dataset import (
    EVALUATION_END,
    EVALUATION_START,
    GROUP_ORDER,
    build_artifact,
    classify_result,
    generate_dataset,
    select_results,
)


def result(trip_id, overall_status, analysis_coverage, review_signals=()):
    common = {
        "codigo_viaje": trip_id, "codigo_vehiculo": "sensitive-vehicle",
        "fecha": "2026-06-01 10:00:00", "reason": "synthetic",
        "distancia_km": 2.0, "baseline": 10.0, "relative_deviation": 0.25,
        "mad": 1.0, "robust_z": 1.0, "baseline_type": "contextual",
        "historical_observations": 100, "distance_range": "> 1 y <= 2",
    }
    return {
        "trip_id": trip_id, "vehicle_id": "sensitive-vehicle",
        "timestamp": "2026-06-01 10:00:00", "distance_km": 2.0,
        "overall_status": overall_status, "analysis_coverage": analysis_coverage,
        "review_signals": list(review_signals),
        "signals": {
            "consumption": {**common, "status": "NO_RELEVANT_DEVIATION", "consumo_litros": 0.2, "consumo_l_100km": 10.0},
            "temporal": {**common, "status": "NO_RELEVANT_DEVIATION", "duration_minutes": 6.0, "minutes_per_km": 3.0},
        },
    }


class ConversationalDatasetTests(unittest.TestCase):
    def test_classifies_the_four_requested_strata(self):
        cases = (
            (result("n", "NO_RELEVANT_DEVIATION", "COMPLETE"), "NO_RELEVANT_DEVIATION_COMPLETE"),
            (result("r", "REVIEW", "COMPLETE", ("consumption",)), "REVIEW_COMPLETE"),
            (result("x", "NOT_EVALUABLE", "NONE"), "NOT_EVALUABLE_NONE"),
            (result("p", "REVIEW", "PARTIAL", ("temporal",)), "PARTIAL"),
        )
        for analytical_result, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(classify_result(analytical_result), expected)

    def test_selection_is_deterministic_limited_and_prefers_review_variety(self):
        inputs = [result(f"n-{index}", "NO_RELEVANT_DEVIATION", "COMPLETE") for index in range(8)]
        inputs += [
            result("r-c", "REVIEW", "COMPLETE", ("consumption",)),
            result("r-t", "REVIEW", "COMPLETE", ("temporal",)),
            result("r-b", "REVIEW", "COMPLETE", ("consumption", "temporal")),
            result("r-c2", "REVIEW", "COMPLETE", ("consumption",)),
        ]
        first, available = select_results(inputs)
        second, _ = select_results(reversed(inputs))
        self.assertEqual(
            [[item["trip_id"] for item in first[group]] for group in GROUP_ORDER],
            [[item["trip_id"] for item in second[group]] for group in GROUP_ORDER],
        )
        self.assertEqual(len(first["NO_RELEVANT_DEVIATION_COMPLETE"]), 5)
        self.assertEqual(available["NO_RELEVANT_DEVIATION_COMPLETE"], 8)
        self.assertEqual(
            {tuple(item["review_signals"]) for item in first["REVIEW_COMPLETE"][:3]},
            {("consumption",), ("temporal",), ("consumption", "temporal")},
        )

    def test_artifact_reports_shortages_and_removes_operational_identity(self):
        artifact = build_artifact([result("real-trip", "NOT_EVALUABLE", "NONE")])
        case = artifact["cases"][0]
        self.assertEqual(artifact["selection"]["NOT_EVALUABLE_NONE"]["shortage"], 4)
        self.assertTrue(case["case_id"].startswith("case_"))
        serialized = json.dumps(case)
        self.assertNotIn("real-trip", serialized)
        self.assertNotIn("sensitive-vehicle", serialized)
        self.assertNotIn("2026-06-01 10:00:00", serialized)
        self.assertEqual(case["signals"]["consumption"]["consumo_l_100km"], 10.0)

    @patch("evaluation.conversational_dataset.AnalyticalService.from_history")
    def test_generation_uses_bulk_repository_methods_and_existing_service(self, from_history):
        repository = MagicMock()
        repository.load_historical_rows.return_value = [{"history": True}]
        repository.load_rows_between.return_value = [{"candidate": True}]
        service = from_history.return_value
        consolidated = MagicMock()
        consolidated.to_dict.return_value = result("trip", "NO_RELEVANT_DEVIATION", "COMPLETE")
        service.evaluate.return_value = consolidated
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "cases.json"
            artifact = generate_dataset(repository, output)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), artifact)
        repository.load_historical_rows.assert_called_once_with()
        repository.load_rows_between.assert_called_once_with(
            EVALUATION_START, EVALUATION_END
        )
        from_history.assert_called_once_with([{"history": True}])
        service.evaluate.assert_called_once_with({"candidate": True})


if __name__ == "__main__":
    unittest.main()
