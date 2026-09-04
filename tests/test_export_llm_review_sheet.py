import csv
import copy
import json
import tempfile
import unittest
from pathlib import Path

from evaluation.export_llm_review_sheet import (
    CSV_COLUMNS,
    EVALUATION_COLUMNS,
    export_file,
    review_rows,
)


def filled_document():
    records = []
    for index in range(1, 21):
        records.append(
            {
                "case_id": f"case_{index:03d}",
                "stratum": "COMPLETE" if index % 2 else "PARTIAL",
                "analytical_result": {
                    "overall_status": "REVIEW",
                    "analysis_coverage": "COMPLETE",
                    "signals": {
                        "consumption": {
                            "status": "REVIEW",
                            "consumo_l_100km": 10.0 + index,
                            "baseline": 10.0,
                            "relative_deviation": index / 10,
                        },
                        "temporal": {
                            "status": "NOT_EVALUABLE" if index == 2 else "REVIEW",
                            **(
                                {}
                                if index == 2
                                else {
                                    "minutes_per_km": 3.0,
                                    "baseline": 2.0,
                                    "relative_deviation": 0.5,
                                }
                            ),
                        },
                    },
                },
                "model": "luna",
                "response": f"Respuesta con acento número {index}",
                "evaluation": {column: 1 for column in EVALUATION_COLUMNS},
            }
        )
    return {"schema_version": 1, "evaluations": records}


class ExportLlmReviewSheetTests(unittest.TestCase):
    def test_rows_keep_order_map_analytical_values_and_blank_scores(self):
        document = filled_document()
        original = copy.deepcopy(document)

        rows = review_rows(document)

        self.assertEqual(document, original)
        self.assertEqual([row["case_id"] for row in rows], [f"case_{i:03d}" for i in range(1, 21)])
        self.assertEqual(rows[0]["consumption_observed"], 11.0)
        self.assertEqual(rows[0]["temporal_relative_deviation"], 0.5)
        self.assertTrue(all(row[column] == "" for row in rows for column in EVALUATION_COLUMNS))

    def test_missing_not_evaluable_values_become_empty_csv_cells(self):
        row = review_rows(filled_document())[1]
        self.assertIsNone(row["temporal_observed"])
        self.assertIsNone(row["temporal_baseline"])
        self.assertIsNone(row["temporal_relative_deviation"])

    def test_export_has_utf8_bom_header_and_twenty_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "filled.json"
            output = root / "nested" / "review.csv"
            source.write_text(json.dumps(filled_document(), ensure_ascii=False), encoding="utf-8")

            export_file(source, output)

            self.assertTrue(output.read_bytes().startswith(b"\xef\xbb\xbf"))
            with output.open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(tuple(rows[0]), CSV_COLUMNS)
            self.assertEqual(len(rows), 20)
            self.assertEqual(rows[1]["temporal_observed"], "")
            self.assertEqual(rows[0]["response"], "Respuesta con acento número 1")

    def test_rejects_case_count_other_than_twenty(self):
        document = filled_document()
        document["evaluations"].pop()
        with self.assertRaisesRegex(ValueError, "20 casos"):
            review_rows(document)

    def test_rejects_duplicate_case_ids(self):
        document = filled_document()
        document["evaluations"][1]["case_id"] = "case_001"
        with self.assertRaisesRegex(ValueError, "duplicados"):
            review_rows(document)

    def test_rejects_empty_response(self):
        document = filled_document()
        document["evaluations"][0]["response"] = "  "
        with self.assertRaisesRegex(ValueError, "response vacía"):
            review_rows(document)

    def test_rejects_missing_minimum_fields(self):
        document = filled_document()
        del document["evaluations"][0]["analytical_result"]["analysis_coverage"]
        with self.assertRaisesRegex(ValueError, "analysis_coverage"):
            review_rows(document)


if __name__ == "__main__":
    unittest.main()
