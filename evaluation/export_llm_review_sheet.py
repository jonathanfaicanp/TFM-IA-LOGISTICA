"""Export a human-review CSV from a filled conversational evaluation file."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("data/conversational_evaluation/luna_evaluation_filled.json")
DEFAULT_OUTPUT = Path("data/conversational_evaluation/luna_review_sheet.csv")
EXPECTED_CASE_COUNT = 20
EVALUATION_COLUMNS = (
    "C1_global_status",
    "C2_signal_statuses",
    "C3_numeric_fidelity",
    "C4_no_unsupported_causes",
    "C5_no_confirmed_inefficiency_claim",
    "C6_not_evaluable_and_coverage",
    "clarity_utility",
    "observations",
)
CSV_COLUMNS = (
    "case_id",
    "stratum",
    "overall_status",
    "coverage",
    "consumption_status",
    "temporal_status",
    "consumption_observed",
    "consumption_baseline",
    "consumption_relative_deviation",
    "temporal_observed",
    "temporal_baseline",
    "temporal_relative_deviation",
    "response",
    *EVALUATION_COLUMNS,
)


def _required(mapping: Mapping[str, Any], field: str, context: str) -> Any:
    if field not in mapping:
        raise ValueError(f"Falta el campo mínimo {field!r} en {context}")
    return mapping[field]


def _validate_records(document: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    records = document.get("evaluations")
    if not isinstance(records, list):
        raise ValueError("El documento debe contener una lista 'evaluations'")
    if len(records) != EXPECTED_CASE_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_CASE_COUNT} casos y se encontraron {len(records)}"
        )
    if not all(isinstance(record, Mapping) for record in records):
        raise ValueError("Cada caso debe ser un objeto JSON")

    case_ids = [_required(record, "case_id", "un caso") for record in records]
    if any(not isinstance(case_id, str) or not case_id.strip() for case_id in case_ids):
        raise ValueError("Cada case_id debe ser texto no vacío")
    duplicates = sorted(
        case_id for case_id, count in Counter(case_ids).items() if count > 1
    )
    if duplicates:
        raise ValueError(f"case_id duplicados: {duplicates}")

    for record in records:
        context = f"el caso {record['case_id']!r}"
        _required(record, "stratum", context)
        response = _required(record, "response", context)
        if not isinstance(response, str) or not response.strip():
            raise ValueError(f"response vacía en {context}")
        analytical = _required(record, "analytical_result", context)
        if not isinstance(analytical, Mapping):
            raise ValueError(f"analytical_result debe ser un objeto en {context}")
        _required(analytical, "overall_status", context)
        _required(analytical, "analysis_coverage", context)
        signals = _required(analytical, "signals", context)
        if not isinstance(signals, Mapping):
            raise ValueError(f"signals debe ser un objeto en {context}")
        for signal_name in ("consumption", "temporal"):
            signal = _required(signals, signal_name, context)
            if not isinstance(signal, Mapping):
                raise ValueError(f"La señal {signal_name!r} debe ser un objeto en {context}")
            _required(signal, "status", context)
    return records


def review_rows(document: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Build review rows without copying or deriving any evaluation scores."""
    rows = []
    for record in _validate_records(document):
        analytical = record["analytical_result"]
        consumption = analytical["signals"]["consumption"]
        temporal = analytical["signals"]["temporal"]
        row = {
            "case_id": record["case_id"],
            "stratum": record["stratum"],
            "overall_status": analytical["overall_status"],
            "coverage": analytical["analysis_coverage"],
            "consumption_status": consumption["status"],
            "temporal_status": temporal["status"],
            "consumption_observed": consumption.get("consumo_l_100km"),
            "consumption_baseline": consumption.get("baseline"),
            "consumption_relative_deviation": consumption.get("relative_deviation"),
            "temporal_observed": temporal.get("minutes_per_km"),
            "temporal_baseline": temporal.get("baseline"),
            "temporal_relative_deviation": temporal.get("relative_deviation"),
            "response": record["response"],
        }
        row.update({column: "" for column in EVALUATION_COLUMNS})
        rows.append(row)
    return rows


def export_file(input_path: Path, output_path: Path) -> list[dict[str, Any]]:
    document = json.loads(input_path.read_text(encoding="utf-8"))
    rows = review_rows(document)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows = export_file(args.input, args.output)
    print(json.dumps({"output": str(args.output), "cases": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
