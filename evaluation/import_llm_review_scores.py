"""Import human review scores from CSV into a filled evaluation artifact."""

from __future__ import annotations

import argparse
import copy
import csv
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any


DEFAULT_REVIEW_SHEET = Path("data/conversational_evaluation/luna_review_sheet.csv")
DEFAULT_EVALUATION_INPUT = Path(
    "data/conversational_evaluation/luna_evaluation_filled.json"
)
DEFAULT_OUTPUT = Path("data/conversational_evaluation/luna_evaluation_scored.json")
EXPECTED_CASE_COUNT = 20
CRITERIA = (
    "C1_global_status",
    "C2_signal_statuses",
    "C3_numeric_fidelity",
    "C4_no_unsupported_causes",
    "C5_no_confirmed_inefficiency_claim",
    "C6_not_evaluable_and_coverage",
)
IMPORTED_COLUMNS = (*CRITERIA, "clarity_utility", "observations")


def _unique_index(
    records: list[Mapping[str, Any]], source: str
) -> dict[str, Mapping[str, Any]]:
    case_ids = []
    for position, record in enumerate(records, start=1):
        case_id = record.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"case_id ausente o vacío en {source}, fila {position}")
        case_ids.append(case_id)
    duplicates = sorted(
        case_id for case_id, count in Counter(case_ids).items() if count > 1
    )
    if duplicates:
        raise ValueError(f"case_id duplicados en {source}: {duplicates}")
    return dict(zip(case_ids, records))


def _validate_score(value: Any, criterion: str, case_id: str) -> int | str:
    if value == "1":
        return 1
    if value == "0":
        return 0
    if value == "N/A":
        return "N/A"
    if value is None or value == "":
        raise ValueError(f"Puntuación vacía para {criterion} en {case_id}")
    raise ValueError(f"Puntuación no válida para {criterion} en {case_id}: {value!r}")


def _validate_clarity(value: Any, case_id: str) -> int:
    if not isinstance(value, str) or value not in {"1", "2", "3", "4", "5"}:
        raise ValueError(
            f"clarity_utility debe ser un entero entre 1 y 5 en {case_id}: {value!r}"
        )
    return int(value)


def import_scores(
    evaluation_document: Mapping[str, Any], csv_records: list[Mapping[str, Any]]
) -> dict[str, Any]:
    """Transfer validated human-entered fields without interpreting responses."""
    evaluations = evaluation_document.get("evaluations")
    if not isinstance(evaluations, list) or not all(
        isinstance(record, Mapping) for record in evaluations
    ):
        raise ValueError("El JSON debe contener una lista de objetos 'evaluations'")
    if len(evaluations) != EXPECTED_CASE_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_CASE_COUNT} casos en el JSON y se encontraron {len(evaluations)}"
        )
    if len(csv_records) != EXPECTED_CASE_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_CASE_COUNT} casos en el CSV y se encontraron {len(csv_records)}"
        )
    if not all(isinstance(record, Mapping) for record in csv_records):
        raise ValueError("Cada fila del CSV debe ser un registro")

    evaluation_by_id = _unique_index(evaluations, "el JSON")
    csv_by_id = _unique_index(csv_records, "el CSV")
    unknown = sorted(set(csv_by_id) - set(evaluation_by_id))
    if unknown:
        raise ValueError(f"case_id desconocidos en el CSV: {unknown}")
    missing = sorted(set(evaluation_by_id) - set(csv_by_id))
    if missing:
        raise ValueError(f"Casos ausentes en el CSV: {missing}")

    validated: dict[str, dict[str, Any]] = {}
    for case_id, csv_record in csv_by_id.items():
        absent_columns = [
            column for column in IMPORTED_COLUMNS if column not in csv_record
        ]
        if absent_columns:
            raise ValueError(f"Columnas ausentes para {case_id}: {absent_columns}")
        observations = csv_record["observations"]
        if observations is None:
            observations = ""
        if not isinstance(observations, str):
            raise ValueError(f"observations debe ser texto en {case_id}")
        validated[case_id] = {
            criterion: _validate_score(csv_record[criterion], criterion, case_id)
            for criterion in CRITERIA
        }
        validated[case_id]["clarity_utility"] = _validate_clarity(
            csv_record["clarity_utility"], case_id
        )
        validated[case_id]["observations"] = observations

    result = copy.deepcopy(evaluation_document)
    for record in result["evaluations"]:
        evaluation = record.get("evaluation")
        if not isinstance(evaluation, dict):
            raise ValueError(
                f"evaluation debe ser un objeto en el caso {record['case_id']!r}"
            )
        evaluation.update(validated[record["case_id"]])
    return result


def import_file(
    review_sheet_path: Path, evaluation_path: Path, output_path: Path
) -> dict[str, Any]:
    evaluation_document = json.loads(evaluation_path.read_text(encoding="utf-8"))
    with review_sheet_path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError("El CSV no contiene una cabecera")
        required = {"case_id", *IMPORTED_COLUMNS}
        missing_columns = sorted(required - set(reader.fieldnames))
        if missing_columns:
            raise ValueError(f"Faltan columnas requeridas en el CSV: {missing_columns}")
        csv_records = list(reader)

    scored = import_scores(evaluation_document, csv_records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(scored, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return scored


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-sheet", type=Path, default=DEFAULT_REVIEW_SHEET)
    parser.add_argument("--evaluation", type=Path, default=DEFAULT_EVALUATION_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    scored = import_file(args.review_sheet, args.evaluation, args.output)
    print(json.dumps({"output": str(args.output), "cases": len(scored["evaluations"])}, indent=2))


if __name__ == "__main__":
    main()
