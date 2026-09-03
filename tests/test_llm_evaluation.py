import json
import tempfile
import unittest
from pathlib import Path

from evaluation.prepare_llm_evaluation import (
    RUBRIC_CRITERIA,
    prepare_document,
    prepare_file,
)
from evaluation.summarize_llm_evaluation import summarize_document


def source_dataset():
    return {
        "schema_version": 1,
        "cases": [
            {
                "case_id": "case_001",
                "stratum": "REVIEW_COMPLETE",
                "overall_status": "REVIEW",
                "analysis_coverage": "COMPLETE",
                "review_signals": ["consumption"],
                "signals": {
                    "consumption": {
                        "status": "REVIEW",
                        "consumo_l_100km": 20.0,
                        "codigo_viaje": "must-not-leak",
                    },
                    "temporal": {
                        "status": "NO_RELEVANT_DEVIATION",
                        "fecha": "2026-01-01 00:00:00",
                    },
                },
                "vehicle_id": "must-not-leak-either",
            },
            {
                "case_id": "case_002",
                "stratum": "PARTIAL",
                "overall_status": "NO_RELEVANT_DEVIATION",
                "analysis_coverage": "PARTIAL",
                "review_signals": [],
                "signals": {},
            },
        ],
    }


class PrepareLlmEvaluationTests(unittest.TestCase):
    def test_generation_is_deterministic_and_preserves_case_identity_and_stratum(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "cases.json"
            first = root / "first.json"
            second = root / "second.json"
            source.write_text(json.dumps(source_dataset()), encoding="utf-8")

            prepare_file(source, first)
            prepare_file(source, second)

            self.assertEqual(first.read_bytes(), second.read_bytes())
            records = json.loads(first.read_text(encoding="utf-8"))["evaluations"]
            self.assertEqual(
                [(record["case_id"], record["stratum"]) for record in records],
                [("case_001", "REVIEW_COMPLETE"), ("case_002", "PARTIAL")],
            )

    def test_output_has_empty_rubric_and_no_sensitive_identifiers(self):
        document = prepare_document(source_dataset())
        record = document["evaluations"][0]
        self.assertIsNone(record["model"])
        self.assertIsNone(record["response"])
        self.assertEqual(
            set(record["evaluation"]),
            {*RUBRIC_CRITERIA, "clarity_utility", "observations"},
        )
        self.assertTrue(all(value is None for value in record["evaluation"].values()))
        serialized = json.dumps(document)
        self.assertNotIn("must-not-leak", serialized)
        self.assertNotIn("codigo_viaje", serialized)
        self.assertNotIn("vehicle_id", serialized)
        self.assertNotIn("fecha", serialized)
        self.assertEqual(
            record["analytical_result"]["signals"]["consumption"]["consumo_l_100km"],
            20.0,
        )


class SummarizeLlmEvaluationTests(unittest.TestCase):
    def test_summary_uses_only_recorded_scores_and_groups_by_stratum(self):
        document = prepare_document(source_dataset())
        first, second = document["evaluations"]
        first["response"] = "This text must not be interpreted."
        first["evaluation"].update(
            dict(zip(RUBRIC_CRITERIA, (1, 0, "N/A", None, 1, 1)))
        )
        first["evaluation"]["clarity_utility"] = 5
        second["evaluation"].update(
            dict(zip(RUBRIC_CRITERIA, (1, 1, 1, 1, 0, "N/A")))
        )
        second["evaluation"]["clarity_utility"] = 3

        summary = summarize_document(document)

        self.assertEqual(summary["total_cases"], 2)
        self.assertEqual(summary["evaluated_cases"], 2)
        self.assertEqual(summary["criteria"]["C1_global_status"]["compliance_pct"], 100.0)
        self.assertEqual(summary["global_compliance_pct"], 77.78)
        self.assertEqual(summary["clarity_utility_mean"], 4.0)
        self.assertEqual(summary["not_applicable_criteria"], 2)
        self.assertEqual(summary["unscored_criteria"], 1)
        self.assertEqual(summary["by_stratum"]["PARTIAL"]["total_cases"], 1)

    def test_null_and_na_are_excluded_from_compliance_denominator(self):
        document = prepare_document(source_dataset())
        record = document["evaluations"][0]
        record["evaluation"]["C1_global_status"] = "N/A"
        summary = summarize_document({"evaluations": [record]})

        criterion = summary["criteria"]["C1_global_status"]
        self.assertEqual(criterion["not_applicable"], 1)
        self.assertIsNone(criterion["compliance_pct"])
        self.assertEqual(summary["evaluated_cases"], 1)
        self.assertEqual(summary["unscored_criteria"], 5)

    def test_invalid_score_is_rejected_instead_of_interpreted(self):
        document = prepare_document(source_dataset())
        document["evaluations"][0]["evaluation"]["C1_global_status"] = "yes"
        with self.assertRaisesRegex(ValueError, "C1_global_status"):
            summarize_document(document)


if __name__ == "__main__":
    unittest.main()
