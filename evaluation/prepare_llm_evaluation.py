"""Prepare deterministic, empty evaluation records from anonymized cases."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("data/conversational_evaluation/cases.json")
DEFAULT_OUTPUT = Path("data/conversational_evaluation/llm_evaluation.json")
RUBRIC_CRITERIA = (
    "C1_global_status",
    "C2_signal_statuses",
    "C3_numeric_fidelity",
    "C4_no_unsupported_causes",
    "C5_no_confirmed_inefficiency_claim",
    "C6_not_evaluable_and_coverage",
)
SENSITIVE_KEYS = {
    "trip_id",
    "vehicle_id",
    "timestamp",
    "codigo_viaje",
    "codigo_vehiculo",
    "fecha",
}


def empty_evaluation() -> dict[str, Any]:
    return {
        **{criterion: None for criterion in RUBRIC_CRITERIA},
        "clarity_utility": None,
        "observations": None,
    }


def _remove_sensitive_fields(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _remove_sensitive_fields(item)
            for key, item in value.items()
            if key not in SENSITIVE_KEYS
        }
    if isinstance(value, list):
        return [_remove_sensitive_fields(item) for item in value]
    return value


def prepare_document(dataset: Mapping[str, Any]) -> dict[str, Any]:
    """Create one blank manual-evaluation record per input case."""
    records = []
    for case in dataset["cases"]:
        analytical_result = {
            key: value
            for key, value in case.items()
            if key not in {"case_id", "stratum"}
        }
        records.append(
            {
                "case_id": case["case_id"],
                "stratum": case["stratum"],
                "analytical_result": _remove_sensitive_fields(analytical_result),
                "model": None,
                "response": None,
                "evaluation": empty_evaluation(),
            }
        )
    return {
        "schema_version": 1,
        "purpose": "manual_llm_response_evaluation",
        "source_schema_version": dataset.get("schema_version"),
        "evaluations": records,
    }


def prepare_file(input_path: Path, output_path: Path) -> dict[str, Any]:
    dataset = json.loads(input_path.read_text(encoding="utf-8"))
    document = prepare_document(dataset)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return document


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    document = prepare_file(args.input, args.output)
    print(json.dumps({"output": str(args.output), "cases": len(document["evaluations"])}, indent=2))


if __name__ == "__main__":
    main()
