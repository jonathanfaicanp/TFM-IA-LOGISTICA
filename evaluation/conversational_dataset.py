"""Build an anonymized, stratified dataset for conversational evaluation.

The module calls the existing AnalyticalService and never changes or
reimplements detector or consolidation decisions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from src.analytical_service import AnalyticalService
from src.consolidation import ConsolidatedResult
from src.sql_repository import SqlHistoricalRepository


DEFAULT_OUTPUT = Path("data/conversational_evaluation/cases.json")
MAX_CASES_PER_GROUP = 5
EVALUATION_START = datetime(2026, 1, 1)
EVALUATION_END = datetime(2027, 1, 1)
GROUP_ORDER = (
    "NO_RELEVANT_DEVIATION_COMPLETE",
    "REVIEW_COMPLETE",
    "NOT_EVALUABLE_NONE",
    "PARTIAL",
)
REVIEW_VARIANTS = (
    ("consumption",),
    ("temporal",),
    ("consumption", "temporal"),
)
IDENTITY_FIELDS = {"codigo_viaje", "codigo_vehiculo", "fecha"}


def classify_result(result: Mapping[str, Any]) -> str | None:
    """Map an analytical result to one requested evaluation stratum."""
    status = result["overall_status"]
    coverage = result["analysis_coverage"]
    if coverage == "PARTIAL":
        return "PARTIAL"
    if status == "NO_RELEVANT_DEVIATION" and coverage == "COMPLETE":
        return "NO_RELEVANT_DEVIATION_COMPLETE"
    if status == "REVIEW" and coverage == "COMPLETE":
        return "REVIEW_COMPLETE"
    if status == "NOT_EVALUABLE" and coverage == "NONE":
        return "NOT_EVALUABLE_NONE"
    return None


def _stable_identity(result: Mapping[str, Any]) -> str:
    raw_identity = "\x1f".join(
        str(result.get(field) or "")
        for field in ("trip_id", "vehicle_id", "timestamp")
    )
    return hashlib.sha256(
        ("tfm-conversational-evaluation-v1\x1f" + raw_identity).encode("utf-8")
    ).hexdigest()


def _select_review_variety(
    candidates: list[Mapping[str, Any]], limit: int
) -> list[Mapping[str, Any]]:
    selected: list[Mapping[str, Any]] = []
    remaining = list(candidates)
    for variant in REVIEW_VARIANTS:
        match = next(
            (item for item in remaining if tuple(item["review_signals"]) == variant),
            None,
        )
        if match is not None and len(selected) < limit:
            selected.append(match)
            remaining.remove(match)
    selected.extend(remaining[: max(0, limit - len(selected))])
    return selected


def select_results(
    results: Iterable[Mapping[str, Any]], limit: int = MAX_CASES_PER_GROUP
) -> tuple[dict[str, list[Mapping[str, Any]]], dict[str, int]]:
    """Deterministically select strata and report every available count."""
    grouped: dict[str, list[Mapping[str, Any]]] = {name: [] for name in GROUP_ORDER}
    for result in results:
        group = classify_result(result)
        if group is not None:
            grouped[group].append(result)
    for candidates in grouped.values():
        candidates.sort(key=_stable_identity)

    available = {name: len(grouped[name]) for name in GROUP_ORDER}
    selected = {
        name: (
            _select_review_variety(grouped[name], limit)
            if name == "REVIEW_COMPLETE"
            else grouped[name][:limit]
        )
        for name in GROUP_ORDER
    }
    return selected, available


def _anonymized_case(
    result: Mapping[str, Any], group: str, case_number: int
) -> dict[str, Any]:
    signals = {
        signal_name: {
            key: value
            for key, value in signal_result.items()
            if key not in IDENTITY_FIELDS
        }
        for signal_name, signal_result in result["signals"].items()
    }
    return {
        "case_id": f"case_{case_number:03d}",
        "stratum": group,
        "overall_status": result["overall_status"],
        "analysis_coverage": result["analysis_coverage"],
        "review_signals": list(result["review_signals"]),
        "signals": signals,
    }


def build_artifact(
    results: Iterable[Mapping[str, Any]], limit: int = MAX_CASES_PER_GROUP
) -> dict[str, Any]:
    selected, available = select_results(results, limit)
    chosen = [
        (group, result)
        for group in GROUP_ORDER
        for result in selected[group]
    ]
    cases = [
        _anonymized_case(result, group, index)
        for index, (group, result) in enumerate(chosen, start=1)
    ]
    selection = {
        group: {
            "requested": limit,
            "available": available[group],
            "selected": len(selected[group]),
            "shortage": max(0, limit - available[group]),
        }
        for group in GROUP_ORDER
    }
    return {
        "schema_version": 1,
        "purpose": "functional_stratified_conversational_evaluation",
        "source_period": {"from": "2026-01-01", "to_exclusive": "2027-01-01"},
        "selection": selection,
        "total_selected": len(cases),
        "cases": cases,
    }


def generate_dataset(
    repository: SqlHistoricalRepository, output_path: Path = DEFAULT_OUTPUT
) -> dict[str, Any]:
    """Read history/candidates in two bulk queries, evaluate, and write JSON."""
    service = AnalyticalService.from_history(repository.load_historical_rows())
    candidates = repository.load_rows_between(EVALUATION_START, EVALUATION_END)
    analytical_results: list[dict[str, Any]] = []
    for candidate in candidates:
        result: ConsolidatedResult = service.evaluate(candidate)
        analytical_results.append(result.to_dict())
    artifact = build_artifact(analytical_results)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    artifact = generate_dataset(
        SqlHistoricalRepository.from_environment(), output_path=args.output
    )
    print(json.dumps({"output": str(args.output), **artifact["selection"]}, indent=2))


if __name__ == "__main__":
    main()
