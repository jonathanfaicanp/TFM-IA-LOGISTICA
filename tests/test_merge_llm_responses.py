import copy
import json
import tempfile
import unittest
from pathlib import Path

from evaluation.merge_llm_responses import merge_documents, merge_files


def evaluation_document():
    return {
        "schema_version": 1,
        "purpose": "manual_llm_response_evaluation",
        "evaluations": [
            {
                "case_id": f"case_{index:03d}",
                "stratum": "TEST",
                "analytical_result": {"status": "REVIEW", "number": index},
                "model": None,
                "response": None,
                "evaluation": {"C1_global_status": None, "observations": None},
            }
            for index in range(1, 21)
        ],
    }


def responses_document():
    return [
        {
            "responses": [
                {
                    "case_id": f"case_{index:03d}",
                    "model": "luna",
                    "response": f"Respuesta {index}",
                    "ignored": "must not be copied",
                }
                for index in reversed(range(1, 21))
            ]
        }
    ]


class MergeLlmResponsesTests(unittest.TestCase):
    def test_matches_by_case_id_and_changes_only_model_and_response(self):
        template = evaluation_document()
        original = copy.deepcopy(template)

        merged = merge_documents(template, responses_document())

        self.assertEqual(template, original)
        for index, (before, after) in enumerate(
            zip(original["evaluations"], merged["evaluations"]), start=1
        ):
            self.assertEqual(after["model"], "luna")
            self.assertEqual(after["response"], f"Respuesta {index}")
            self.assertEqual(
                {key: value for key, value in after.items() if key not in {"model", "response"}},
                {key: value for key, value in before.items() if key not in {"model", "response"}},
            )
            self.assertNotIn("ignored", after)

    def test_writes_the_merged_document(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evaluation_path = root / "llm_evaluation.json"
            responses_path = root / "luna_responses.json"
            output_path = root / "nested" / "luna_evaluation_filled.json"
            evaluation_path.write_text(json.dumps(evaluation_document()), encoding="utf-8")
            responses_path.write_text(json.dumps(responses_document()), encoding="utf-8")

            merged = merge_files(evaluation_path, responses_path, output_path)

            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8")), merged)

    def test_rejects_a_response_count_other_than_twenty(self):
        responses = responses_document()
        responses[0]["responses"].pop()
        with self.assertRaisesRegex(ValueError, "20 respuestas"):
            merge_documents(evaluation_document(), responses)

    def test_rejects_duplicate_response_case_id(self):
        responses = responses_document()
        responses[0]["responses"][0]["case_id"] = responses[0]["responses"][1]["case_id"]
        with self.assertRaisesRegex(ValueError, "duplicados"):
            merge_documents(evaluation_document(), responses)

    def test_rejects_duplicate_evaluation_case_id(self):
        template = evaluation_document()
        template["evaluations"][0]["case_id"] = template["evaluations"][1]["case_id"]
        with self.assertRaisesRegex(ValueError, "duplicados"):
            merge_documents(template, responses_document())

    def test_rejects_unknown_case_id(self):
        responses = responses_document()
        responses[0]["responses"][0]["case_id"] = "unknown"
        with self.assertRaisesRegex(ValueError, "desconocidos"):
            merge_documents(evaluation_document(), responses)

    def test_rejects_a_case_without_response(self):
        template = evaluation_document()
        template["evaluations"].append(
            {**copy.deepcopy(template["evaluations"][0]), "case_id": "case_021"}
        )
        with self.assertRaisesRegex(ValueError, "sin respuesta"):
            merge_documents(template, responses_document())

    def test_rejects_invalid_wrapper_and_missing_payload_fields(self):
        with self.assertRaisesRegex(ValueError, "estructura"):
            merge_documents(evaluation_document(), {"responses": []})

        responses = responses_document()
        del responses[0]["responses"][0]["model"]
        with self.assertRaisesRegex(ValueError, "Faltan campos"):
            merge_documents(evaluation_document(), responses)


if __name__ == "__main__":
    unittest.main()
