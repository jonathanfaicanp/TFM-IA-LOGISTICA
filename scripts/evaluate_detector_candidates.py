"""Aggregate experimental D1/D2/D3 candidate-rule evaluation for 2026.

Construction is limited to 2024-2025 B30/MAD scopes. Rules are descriptive
scenarios only: output contains aggregates, never alerts or individual trips.

The temporal split is configurable; defaults preserve the original experiment.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from analyze_b30_mad import build_scopes, robust_z, select_b30_scope
from experimental_split import validate_split
from compare_baselines import RANGES, distance_range, number, parse_number, parse_start_date, write_csv


def relative_deviation(value: float, baseline: float) -> float:
    return (value - baseline) / baseline


def rule_and(relative: float, score: float | None, relative_threshold: float, score_threshold: float) -> bool:
    return score is not None and relative > relative_threshold and score > score_threshold


def rule_or(relative: float, score: float | None, relative_threshold: float, score_threshold: float) -> bool:
    return relative > relative_threshold or (score is not None and score > score_threshold)


def minimal_vehicles_for_half(records: list[dict]) -> int:
    if not records:
        return 0
    target, cumulative = len(records) / 2, 0
    for position, count in enumerate(sorted(Counter(record["vehicle"] for record in records).values(), reverse=True), start=1):
        cumulative += count
        if cumulative >= target:
            return position
    raise RuntimeError("unreachable")


def percentage(part: int, total: int) -> float:
    return number(100 * part / total) if total else 0.0


def load_records(input_path: Path, history_years: tuple[int, ...] = (2024, 2025), evaluation_year: int = 2026) -> tuple[list[dict], list[dict]]:
    validate_split(history_years, evaluation_year)
    history, evaluation = [], []
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file, delimiter=";"):
            date = parse_start_date(row["Fecha de inicio"])
            if date.year not in (*history_years, evaluation_year):
                continue
            distance_km = parse_number(row["Distancia"]) / 1000
            consumption_liters = parse_number(row["Consumo"]) / 1000
            if distance_km <= 0 or consumption_liters <= 0:
                continue
            record = {"vehicle": row["Codigo Vehiculo"], "range": distance_range(distance_km), "distance_km": distance_km, "l_100km": consumption_liters / distance_km * 100}
            (evaluation if date.year == evaluation_year else history).append(record)
    return history, evaluation


def evaluate_records(history: list[dict], evaluation: list[dict]) -> list[dict]:
    scopes_history = [{key: record[key] for key in ("vehicle", "range", "l_100km")} for record in history]
    vehicles, contexts = build_scopes(scopes_history)
    result = []
    for record in evaluation:
        scope = select_b30_scope(record, vehicles, contexts)
        if scope is None:
            continue
        centre, _, scale, baseline_type = scope
        result.append({**record, "baseline_type": baseline_type, "relative": relative_deviation(record["l_100km"], centre), "robust_z": robust_z(record["l_100km"], centre, scale)})
    return result


def scenario_definitions() -> list[tuple[str, str, float, float | None, str | None]]:
    scenarios = [(f"D1_relative_gt_{int(level * 100)}pct", "D1", level, None, None) for level in (.25, .5, 1, 2, 5)]
    scenarios.extend((f"D2_robust_z_gt_{level}", "D2", float(level), None, None) for level in (2, 3, 4, 5, 10))
    for operation in ("AND", "OR"):
        for relative, score in ((.5, 2), (1, 3), (2, 5)):
            scenarios.append((f"D3_{operation}_relative_gt_{int(relative * 100)}pct_z_gt_{score}", "D3", relative, float(score), operation))
    return scenarios


def applicable_records(records: list[dict], family: str) -> list[dict]:
    return records if family == "D1" else [record for record in records if record["robust_z"] is not None]


def marked_records(records: list[dict], family: str, first: float, second: float | None, operation: str | None) -> list[dict]:
    if family == "D1":
        return [record for record in records if record["relative"] > first]
    if family == "D2":
        return [record for record in records if record["robust_z"] > first]
    if operation == "AND":
        return [record for record in records if rule_and(record["relative"], record["robust_z"], first, second)]
    return [record for record in records if rule_or(record["relative"], record["robust_z"], first, second)]


def group_percentage(records: list[dict], marked: list[dict], predicate) -> float:
    denominator = sum(predicate(record) for record in records)
    numerator = sum(predicate(record) for record in marked)
    return percentage(numerator, denominator)


def summarize_scenario(name: str, family: str, first: float, second: float | None, operation: str | None, all_records: list[dict]) -> tuple[dict, list[dict]]:
    eligible = applicable_records(all_records, family)
    marked = marked_records(eligible, family, first, second, operation)
    summary = {
        "scenario": name, "family": family, "relative_threshold": first if family != "D2" else None,
        "robust_z_threshold": first if family == "D2" else second, "operation": operation,
        "records_evaluable": len(eligible), "records_marked": len(marked), "marked_pct": percentage(len(marked), len(eligible)),
        "vehicles_affected": len({record["vehicle"] for record in marked}), "vehicles_for_at_least_50pct_of_marked": minimal_vehicles_for_half(marked),
        "pct_marked_distance_lte_1km": group_percentage(eligible, marked, lambda record: record["distance_km"] <= 1),
        "pct_marked_distance_gt_5km": group_percentage(eligible, marked, lambda record: record["distance_km"] > 5),
        "pct_marked_distance_gt_20km": group_percentage(eligible, marked, lambda record: record["distance_km"] > 20),
    }
    range_rows = []
    for range_name in RANGES:
        evaluated_count = sum(record["range"] == range_name for record in eligible)
        marked_count = sum(record["range"] == range_name for record in marked)
        range_rows.append({"scenario": name, "family": family, "rango_distancia_km": range_name, "registros_evaluables": evaluated_count, "registros_marcados": marked_count, "porcentaje_marcado_en_rango": percentage(marked_count, evaluated_count), "porcentaje_de_marcados_en_rango": percentage(marked_count, len(marked))})
    return summary, range_rows


def run(input_path: Path, output_dir: Path, history_years: tuple[int, ...] = (2024, 2025), evaluation_year: int = 2026) -> tuple[list[dict], list[dict]]:
    history, evaluation = load_records(input_path, history_years, evaluation_year)
    all_records = evaluate_records(history, evaluation)
    summaries, range_rows = [], []
    for definition in scenario_definitions():
        summary, rows = summarize_scenario(*definition, all_records)
        summaries.append(summary); range_rows.extend(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / f"detector_candidate_scenarios_{evaluation_year}.csv", list(summaries[0]), summaries)
    write_csv(output_dir / f"detector_candidate_scenarios_by_range_{evaluation_year}.csv", list(range_rows[0]), range_rows)
    return summaries, range_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/datos_operativa.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--history-years", type=int, nargs="+", default=[2024, 2025])
    parser.add_argument("--evaluation-year", type=int, default=2026)
    args = parser.parse_args()
    summaries, _ = run(args.input, args.output_dir, tuple(args.history_years), args.evaluation_year)
    print(f"Escenarios evaluados: {len(summaries)}")


if __name__ == "__main__":
    main()
