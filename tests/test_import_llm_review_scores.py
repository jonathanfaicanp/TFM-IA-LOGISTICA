import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

from evaluation.import_llm_review_scores import (
    CRITERIA,
    IMPORTED_COLUMNS,
    import_file,
    import_scores,
)


def evaluation_document():
    return {
        "schema_version": 1,
        "evaluations": [
            {
                "case_id": f"case_{index:03d}",
                "stratum": "TEST",
                "analytical_result": {"overall_status": "REVIEW", "number": index},
                "model": "luna",
                "response": f"Respuesta {index}",
                "evaluation": {
                    **{criterion: None for criterion in CRITERIA},
                    "clarity_utility": None,
                    "observations": None,
                },
            }
            for index in range(1, 21)
        ],
    }


def csv_records():
    return [
        {
            "case_id": f"case_{index:03d}",
            **{
                criterion: ("N/A" if criterion == "C3_numeric_fidelity" else str(index % 2))
                for criterion in CRITERIA
            },
            "clarity_utility": str((index - 1) % 5 + 1),
            "observations": "" if index % 2 else f"Nota {index}",
            "response": "Esta columna no debe importarse",
        }
        for index in reversed(range(1, 21))
    ]


class ImportLlmReviewScoresTests(unittest.TestCase):
    def test_matches_by_case_id_and_only_changes_evaluation_fields(self):
        source = evaluation_document()
        original = copy.deepcopy(source)

        scored = import_scores(source, csv_records())

        self.assertEqual(source, original)
        for index, (before, after) in enumerate(
            zip(original["evaluations"], scored["evaluations"]), start=1
        ):
            for field in ("case_id", "stratum", "analytical_result", "model", "response"):
                self.assertEqual(after[field], before[field])
            self.assertEqual(after["evaluation"]["C1_global_status"], index % 2)
            self.assertEqual(after["evaluation"]["C3_numeric_fidelity"], "N/A")
            self.assertEqual(after["evaluation"]["clarity_utility"], (index - 1) % 5 + 1)

    def test_import_file_reads_bom_and_writes_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sheet = root / "review.csv"
            source = root / "filled.json"
            output = root / "nested" / "scored.json"
            source.write_text(json.dumps(evaluation_document()), encoding="utf-8")
            with sheet.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=("case_id", *IMPORTED_COLUMNS))
                writer.writeheader()
                writer.writerows(
                    {key: row[key] for key in ("case_id", *IMPORTED_COLUMNS)}
                    for row in csv_records()
                )

            scored = import_file(sheet, source, output)

            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), scored)

    def test_rejects_wrong_case_count_and_duplicates(self):
        short_rows = csv_records()[:-1]
        with self.assertRaisesRegex(ValueError, "20 casos en el CSV"):
            import_scores(evaluation_document(), short_rows)

        rows = csv_records()
        rows[0]["case_id"] = rows[1]["case_id"]
        with self.assertRaisesRegex(ValueError, "duplicados"):
            import_scores(evaluation_document(), rows)

    def test_rejects_unknown_and_missing_case_ids(self):
        rows = csv_records()
        rows[0]["case_id"] = "unknown"
        with self.assertRaisesRegex(ValueError, "desconocidos"):
            import_scores(evaluation_document(), rows)

    def test_rejects_blank_or_invalid_criterion_score(self):
        for invalid in ("", "2", "n/a", " 1"):
            with self.subTest(invalid=invalid):
                rows = csv_records()
                rows[0]["C1_global_status"] = invalid
                with self.assertRaisesRegex(ValueError, "Puntuación"):
                    import_scores(evaluation_document(), rows)

    def test_rejects_invalid_clarity(self):
        for invalid in ("", "0", "6", "1.0", "three"):
            with self.subTest(invalid=invalid):
                rows = csv_records()
                rows[0]["clarity_utility"] = invalid
                with self.assertRaisesRegex(ValueError, "entero entre 1 y 5"):
                    import_scores(evaluation_document(), rows)

    def test_requires_all_imported_columns(self):
        rows = csv_records()
        del rows[0]["observations"]
        with self.assertRaisesRegex(ValueError, "Columnas ausentes"):
            import_scores(evaluation_document(), rows)


if __name__ == "__main__":
    unittest.main()
