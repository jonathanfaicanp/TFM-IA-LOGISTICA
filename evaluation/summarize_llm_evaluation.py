"""Summarize manually recorded scores without evaluating LLM responses."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .prepare_llm_evaluation import DEFAULT_OUTPUT, RUBRIC_CRITERIA


DEFAULT_SUMMARY_OUTPUT = Path("data/conversational_evaluation/llm_evaluation_summary.json")


def _validate_score(value: Any, criterion: str) -> None:
    if value is None or value == "N/A":
        return
    if isinstance(value, bool) or value not in (0, 1):
        raise ValueError(f"Valor no válido para {criterion}: {value!r}")


def _validate_clarity(value: Any) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
        raise ValueError(f"Valor no válido para clarity_utility: {value!r}")


def _percentage(compliant: int, applicable: int) -> float | None:
    return round(100 * compliant / applicable, 2) if applicable else None


def _score_block(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    records = list(records)
    criteria: dict[str, dict[str, int | float | None]] = {}
    total_compliant = total_applicable = total_na = total_null = 0
    clarity_values: list[int] = []
    evaluated_cases = 0

    for record in records:
        evaluation = record["evaluation"]
        values = [evaluation[criterion] for criterion in RUBRIC_CRITERIA]
        for criterion, value in zip(RUBRIC_CRITERIA, values):
            _validate_score(value, criterion)
        clarity = evaluation["clarity_utility"]
        _validate_clarity(clarity)
        if any(value is not None for value in values) or clarity is not None:
            evaluated_cases += 1
        if clarity is not None:
            clarity_values.append(clarity)

    for criterion in RUBRIC_CRITERIA:
        values = [record["evaluation"][criterion] for record in records]
        compliant = sum(value == 1 for value in values)
        non_compliant = sum(value == 0 for value in values)
        not_applicable = sum(value == "N/A" for value in values)
        unscored = sum(value is None for value in values)
        applicable = compliant + non_compliant
        criteria[criterion] = {
            "compliant": compliant,
            "non_compliant": non_compliant,
            "applicable": applicable,
            "not_applicable": not_applicable,
            "unscored": unscored,
            "compliance_pct": _percentage(compliant, applicable),
        }
        total_compliant += compliant
        total_applicable += applicable
        total_na += not_applicable
        total_null += unscored

    return {
        "total_cases": len(records),
        "evaluated_cases": evaluated_cases,
        "criteria": criteria,
        "global_compliance_pct": _percentage(total_compliant, total_applicable),
        "clarity_utility_mean": (
            round(sum(clarity_values) / len(clarity_values), 2)
            if clarity_values
            else None
        ),
        "not_applicable_criteria": total_na,
        "unscored_criteria": total_null,
    }


def summarize_document(document: Mapping[str, Any]) -> dict[str, Any]:
    records = list(document["evaluations"])
    strata = sorted({record["stratum"] for record in records})
    return {
        "schema_version": 1,
        **_score_block(records),
        "by_stratum": {
            stratum: _score_block(
                record for record in records if record["stratum"] == stratum
            )
            for stratum in strata
        },
    }


def summarize_file(input_path: Path, output_path: Path) -> dict[str, Any]:
    document = json.loads(input_path.read_text(encoding="utf-8"))
    summary = summarize_document(document)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    args = parser.parse_args()
    summary = summarize_file(args.input, args.output)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
