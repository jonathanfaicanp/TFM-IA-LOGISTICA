"""Robust descriptive analysis of 2026 minutes/km against 2024-2025 history.

The output describes temporal deviation for comparable-distance trips. It does
not classify causes, implement a temporal detector or select thresholds.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from analyze_duration_distance_feasibility import transform_duration_distance
from compare_baselines import RANGES, distance_range, number, parse_number, parse_start_date, percentile


MAD_SCALE = 1.4826
MINIMUM_VEHICLE_OBSERVATIONS = 100
MINIMUM_CONTEXT_OBSERVATIONS = 30
RELATIVE_THRESHOLDS = (.25, .50, 1.0, 2.0)
Z_THRESHOLDS = (2, 3, 4, 5)
AND_RULES = ((.50, 2), (1.0, 3), (2.0, 5))


def median_mad(values: list[float]) -> tuple[float, float]:
    centre = median(values)
    return centre, median(abs(value - centre) for value in values)


def robust_z(value: float, centre: float, mad: float) -> float | None:
    return None if mad == 0 else (value - centre) / (MAD_SCALE * mad)


def build_scopes(history: list[dict]) -> tuple[dict, dict]:
    by_vehicle: dict[str, list[float]] = defaultdict(list)
    by_context: dict[tuple[str, str], list[float]] = defaultdict(list)
    for record in history:
        by_vehicle[record["vehicle"]].append(record["minutes_per_km"])
        by_context[(record["vehicle"], record["range"])].append(record["minutes_per_km"])
    eligible = {vehicle for vehicle, values in by_vehicle.items() if len(values) >= MINIMUM_VEHICLE_OBSERVATIONS}
    vehicles = {vehicle: (*median_mad(by_vehicle[vehicle]), len(by_vehicle[vehicle]), "vehicle_fallback") for vehicle in eligible}
    contexts = {
        key: (*median_mad(values), len(values), "contextual")
        for key, values in by_context.items()
        if key[0] in eligible and len(values) >= MINIMUM_CONTEXT_OBSERVATIONS
    }
    return vehicles, contexts


def select_scope(record: dict, vehicles: dict, contexts: dict):
    return contexts.get((record["vehicle"], record["range"])) or vehicles.get(record["vehicle"])


def distribution(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {name: None for name in ("median", "p75", "p90", "p95", "p99", "max")}
    return {
        "median": number(median(values)),
        "p75": number(percentile(values, .75)),
        "p90": number(percentile(values, .90)),
        "p95": number(percentile(values, .95)),
        "p99": number(percentile(values, .99)),
        "max": number(max(values)),
    }


def percentage(count: int, total: int) -> float:
    return number(100 * count / total) if total else 0.0


def candidate_rates(records: list[dict]) -> dict[str, float]:
    total = len(records)
    result = {f"relative_gt_{int(threshold * 100)}pct": percentage(sum(record["relative_deviation"] > threshold for record in records), total) for threshold in RELATIVE_THRESHOLDS}
    result.update({f"robust_z_gt_{threshold}": percentage(sum(record["robust_z"] > threshold for record in records), total) for threshold in Z_THRESHOLDS})
    result.update({f"relative_gt_{int(relative * 100)}pct_AND_z_gt_{score}": percentage(sum(record["relative_deviation"] > relative and record["robust_z"] > score for record in records), total) for relative, score in AND_RULES})
    return result


def group_summary(records: list[dict]) -> dict:
    return {
        "n": len(records),
        "relative_deviation": distribution([record["relative_deviation"] for record in records]),
        "robust_z": distribution([record["robust_z"] for record in records]),
        "candidate_rule_percentages": candidate_rates(records),
    }


def load_records(input_path: Path) -> tuple[list[dict], list[dict]]:
    history, evaluation = [], []
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file, delimiter=";"):
            start = parse_start_date(row["Fecha de inicio"])
            if start.year not in (2024, 2025, 2026):
                continue
            duration = parse_number(row["Duracion"])
            distance = parse_number(row["Distancia"])
            reason = None
            if duration <= 0:
                reason = "NON_POSITIVE_DURATION"
            elif distance <= 0:
                reason = "NON_POSITIVE_DISTANCE"
            record = {"vehicle": row["Codigo Vehiculo"], "year": start.year, "reason": reason}
            if reason is None:
                distance_km, duration_minutes, minutes_per_km = transform_duration_distance(duration, distance)
                record.update({"distance_km": distance_km, "range": distance_range(distance_km), "duration_minutes": duration_minutes, "minutes_per_km": minutes_per_km})
            if start.year == 2026:
                evaluation.append(record)
            elif reason is None:
                history.append(record)
    return history, evaluation


def analyze(history: list[dict], evaluation: list[dict]) -> dict:
    vehicles, contexts = build_scopes(history)
    evaluated = []
    not_evaluable = Counter()
    baseline_types = Counter()
    mad_zero = 0
    for record in evaluation:
        if record["reason"] is not None:
            not_evaluable[record["reason"]] += 1
            continue
        scope = select_scope(record, vehicles, contexts)
        if scope is None:
            not_evaluable["NO_HISTORICAL_BASELINE"] += 1
            continue
        centre, mad, historical_observations, baseline_type = scope
        if mad == 0:
            mad_zero += 1
            not_evaluable["ZERO_HISTORICAL_MAD"] += 1
            continue
        score = robust_z(record["minutes_per_km"], centre, mad)
        evaluated.append({**record, "baseline": centre, "mad": mad, "historical_observations": historical_observations, "baseline_type": baseline_type, "relative_deviation": (record["minutes_per_km"] - centre) / centre, "robust_z": score})
        baseline_types[baseline_type] += 1

    valid = sum(record["reason"] is None for record in evaluation)
    return {
        "total_2026": len(evaluation),
        "valid_temporal_2026": valid,
        "evaluable_2026": len(evaluated),
        "coverage_pct_of_valid_temporal": percentage(len(evaluated), valid),
        "baseline_type": dict(baseline_types),
        "not_evaluable": {"total": sum(not_evaluable.values()), "reasons": dict(not_evaluable)},
        "mad_zero": mad_zero,
        "groups": {
            "all_evaluable": group_summary(evaluated),
            "distance_lte_1km": group_summary([record for record in evaluated if record["distance_km"] <= 1]),
            "distance_gt_1km": group_summary([record for record in evaluated if record["distance_km"] > 1]),
        },
    }


def run(input_path: Path) -> dict:
    return analyze(*load_records(input_path))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/datos_operativa.csv"))
    args = parser.parse_args()
    print(json.dumps(run(args.input), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
