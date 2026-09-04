"""Merge recorded LLM responses into the conversational evaluation template."""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any


DEFAULT_EVALUATION_INPUT = Path("data/conversational_evaluation/llm_evaluation.json")
DEFAULT_RESPONSES_INPUT = Path("data/conversational_evaluation/luna_responses.json")
DEFAULT_OUTPUT = Path(
    "data/conversational_evaluation/luna_evaluation_filled.json"
)
EXPECTED_RESPONSE_COUNT = 20


def _response_records(document: Any) -> list[Mapping[str, Any]]:
    if not isinstance(document, list) or len(document) != 1:
        raise ValueError("luna_responses.json debe tener la estructura [{\"responses\": [...]}]")
    wrapper = document[0]
    if not isinstance(wrapper, Mapping) or not isinstance(wrapper.get("responses"), list):
        raise ValueError("luna_responses.json debe tener la estructura [{\"responses\": [...]}]")
    records = wrapper["responses"]
    if len(records) != EXPECTED_RESPONSE_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_RESPONSE_COUNT} respuestas y se encontraron {len(records)}"
        )
    if not all(isinstance(record, Mapping) for record in records):
        raise ValueError("Cada respuesta debe ser un objeto JSON")
    return records


def _index_unique(records: list[Mapping[str, Any]], source: str) -> dict[Any, Mapping[str, Any]]:
    missing = [index for index, record in enumerate(records) if "case_id" not in record]
    if missing:
        raise ValueError(f"Falta case_id en {source}, posiciones: {missing}")
    counts = Counter(record["case_id"] for record in records)
    duplicates = sorted((case_id for case_id, count in counts.items() if count > 1), key=str)
    if duplicates:
        raise ValueError(f"case_id duplicados en {source}: {duplicates}")
    return {record["case_id"]: record for record in records}


def merge_documents(
    evaluation_document: Mapping[str, Any], responses_document: Any
) -> dict[str, Any]:
    """Return a copy of the template with only model and response populated."""
    evaluations = evaluation_document.get("evaluations")
    if not isinstance(evaluations, list):
        raise ValueError("llm_evaluation.json debe contener una lista 'evaluations'")
    if not all(isinstance(record, Mapping) for record in evaluations):
        raise ValueError("Cada evaluación debe ser un objeto JSON")

    evaluation_by_id = _index_unique(evaluations, "llm_evaluation.json")
    responses = _response_records(responses_document)
    response_by_id = _index_unique(responses, "luna_responses.json")

    unknown = sorted(set(response_by_id) - set(evaluation_by_id), key=str)
    if unknown:
        raise ValueError(f"case_id desconocidos: {unknown}")
    missing = sorted(set(evaluation_by_id) - set(response_by_id), key=str)
    if missing:
        raise ValueError(f"Casos sin respuesta: {missing}")

    for case_id, record in response_by_id.items():
        absent_fields = [field for field in ("model", "response") if field not in record]
        if absent_fields:
            raise ValueError(f"Faltan campos en la respuesta {case_id!r}: {absent_fields}")

    merged = copy.deepcopy(evaluation_document)
    for evaluation in merged["evaluations"]:
        response = response_by_id[evaluation["case_id"]]
        evaluation["model"] = response["model"]
        evaluation["response"] = response["response"]
    return merged


def merge_files(
    evaluation_path: Path, responses_path: Path, output_path: Path
) -> dict[str, Any]:
    evaluation_document = json.loads(evaluation_path.read_text(encoding="utf-8"))
    responses_document = json.loads(responses_path.read_text(encoding="utf-8"))
    merged = merge_documents(evaluation_document, responses_document)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation", type=Path, default=DEFAULT_EVALUATION_INPUT)
    parser.add_argument("--responses", type=Path, default=DEFAULT_RESPONSES_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    merged = merge_files(args.evaluation, args.responses, args.output)
    print(json.dumps({"output": str(args.output), "cases": len(merged["evaluations"])}, indent=2))


if __name__ == "__main__":
    main()
