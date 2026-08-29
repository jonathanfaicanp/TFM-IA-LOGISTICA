"""Semi-synthetic benchmark for candidate temporal rules on trips over 1 km.

Perturbations affect duration only and remain in memory. Metrics describe a
controlled experimental benchmark, not performance against real inefficiency.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from analyze_duration_distance_feasibility import transform_duration_distance
from analyze_temporal_robustness import build_scopes, robust_z, select_scope
from compare_baselines import distance_range, number, parse_number, parse_start_date, write_csv


PERTURBATIONS = (.25, .50, 1.0, 2.0, 5.0)
RULES = (
    ("D1_relative_gt_50pct", "D1", .5, None, None),
    ("D1_relative_gt_100pct", "D1", 1.0, None, None),
    ("D1_relative_gt_200pct", "D1", 2.0, None, None),
    ("D2_robust_z_gt_2", "D2", 2.0, None, None),
    ("D2_robust_z_gt_3", "D2", 3.0, None, None),
    ("D2_robust_z_gt_5", "D2", 5.0, None, None),
    ("D3_AND_relative_gt_50pct_z_gt_2", "D3", .5, 2.0, "AND"),
    ("D3_AND_relative_gt_100pct_z_gt_3", "D3", 1.0, 3.0, "AND"),
    ("D3_AND_relative_gt_200pct_z_gt_5", "D3", 2.0, 5.0, "AND"),
    ("D3_OR_relative_gt_50pct_z_gt_2", "D3", .5, 2.0, "OR"),
    ("D3_OR_relative_gt_100pct_z_gt_3", "D3", 1.0, 3.0, "OR"),
    ("D3_OR_relative_gt_200pct_z_gt_5", "D3", 2.0, 5.0, "OR"),
)


def normalize_temporal_record(row: dict) -> dict | None:
    duration_seconds = parse_number(row["Duracion"])
    distance_meters = parse_number(row["Distancia"])
    if duration_seconds <= 0 or distance_meters <= 1000:
        return None
    distance_km, duration_minutes, minutes_per_km = transform_duration_distance(duration_seconds, distance_meters)
    return {
        "vehicle": row["Codigo Vehiculo"],
        "year": parse_start_date(row["Fecha de inicio"]).year,
        "distance_km": distance_km,
        "duration_minutes": duration_minutes,
        "minutes_per_km": minutes_per_km,
        "range": distance_range(distance_km),
    }


def perturb_record(record: dict, perturbation: float) -> dict:
    duration_minutes = record["duration_minutes"] * (1 + perturbation)
    return {**record, "duration_minutes": duration_minutes, "minutes_per_km": duration_minutes / record["distance_km"]}


def relative_deviation(value: float, baseline: float) -> float:
    return (value - baseline) / baseline


def apply_rule(relative: float, score: float, family: str, first: float, second: float | None, operation: str | None) -> bool:
    if family == "D1":
        return relative > first
    if family == "D2":
        return score > first
    if operation == "AND":
        return relative > first and score > second
    return relative > first or score > second


def aggregate_rates(positives: int, detected: int, controls: int, control_marked: int) -> dict:
    recall = percentage(detected, positives)
    marked = percentage(control_marked, controls)
    specificity = number(100 - marked)
    return {
        "cases_perturbed_evaluable": positives,
        "detected": detected,
        "recall_pct": recall,
        "false_negative_rate_pct": number(100 - recall),
        "control_cases": controls,
        "control_marked": control_marked,
        "control_marked_pct_experimental": marked,
        "specificity_pct_experimental": specificity,
        "balanced_accuracy_pct": number((recall + specificity) / 2),
        "youden_j_pct_points": number(recall + specificity - 100),
    }


def percentage(count: int, total: int) -> float:
    return number(100 * count / total) if total else 0.0


def load_records(input_path: Path) -> tuple[list[dict], list[dict]]:
    history, evaluation = [], []
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file, delimiter=";"):
            year = parse_start_date(row["Fecha de inicio"]).year
            if year not in (2024, 2025, 2026):
                continue
            record = normalize_temporal_record(row)
            if record is None:
                continue
            (evaluation if year == 2026 else history).append(record)
    return history, evaluation


def prepare_evaluation(history: list[dict], evaluation: list[dict]) -> list[dict]:
    vehicles, contexts = build_scopes(history)
    prepared = []
    for record in evaluation:
        scope = select_scope(record, vehicles, contexts)
        if scope is None:
            continue
        centre, mad, historical_observations, baseline_type = scope
        if mad == 0:
            continue
        prepared.append({**record, "baseline": centre, "mad": mad, "historical_observations": historical_observations, "baseline_type": baseline_type})
    return prepared


def evaluate_rule(records: list[dict], perturbation: float, rule: tuple) -> dict:
    _, family, first, second, operation = rule
    control_marked = 0
    detected = 0
    for record in records:
        control_relative = relative_deviation(record["minutes_per_km"], record["baseline"])
        control_score = robust_z(record["minutes_per_km"], record["baseline"], record["mad"])
        control_marked += apply_rule(control_relative, control_score, family, first, second, operation)
        perturbed = perturb_record(record, perturbation)
        perturbed_relative = relative_deviation(perturbed["minutes_per_km"], record["baseline"])
        perturbed_score = robust_z(perturbed["minutes_per_km"], record["baseline"], record["mad"])
        detected += apply_rule(perturbed_relative, perturbed_score, family, first, second, operation)
    return aggregate_rates(len(records), detected, len(records), control_marked)


def build_comparison(summary_rows: list[dict]) -> list[dict]:
    comparison = []
    for name, family, relative_threshold, robust_threshold, operation in RULES:
        rows = [row for row in summary_rows if row["scenario"] == name]
        first = rows[0]
        result = {
            "scenario": name,
            "family": family,
            "relative_threshold": relative_threshold if family != "D2" else None,
            "robust_z_threshold": relative_threshold if family == "D2" else robust_threshold,
            "operation": operation,
            "evaluable_records": first["control_cases"],
            "control_marked_pct_experimental": first["control_marked_pct_experimental"],
            "specificity_pct_experimental": first["specificity_pct_experimental"],
        }
        for row in rows:
            level = row["perturbation_pct"]
            result[f"recall_pct_plus_{level}"] = row["recall_pct"]
            result[f"false_negative_rate_pct_plus_{level}"] = row["false_negative_rate_pct"]
            result[f"balanced_accuracy_pct_plus_{level}"] = row["balanced_accuracy_pct"]
            result[f"youden_j_pct_points_plus_{level}"] = row["youden_j_pct_points"]
        comparison.append(result)
    return comparison


def run(input_path: Path, output_dir: Path) -> tuple[list[dict], list[dict]]:
    history, evaluation = load_records(input_path)
    prepared = prepare_evaluation(history, evaluation)
    summary_rows = []
    for perturbation in PERTURBATIONS:
        for rule in RULES:
            name, family, relative_threshold, robust_threshold, operation = rule
            summary_rows.append({
                "perturbation_pct": int(perturbation * 100),
                "scenario": name,
                "family": family,
                "relative_threshold": relative_threshold if family != "D2" else None,
                "robust_z_threshold": relative_threshold if family == "D2" else robust_threshold,
                "operation": operation,
                **evaluate_rule(prepared, perturbation, rule),
            })
    comparison = build_comparison(summary_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "temporal_synthetic_benchmark_summary.csv", list(summary_rows[0]), summary_rows)
    write_csv(output_dir / "temporal_synthetic_benchmark_rule_comparison.csv", list(comparison[0]), comparison)
    return summary_rows, comparison


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/datos_operativa.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    _, comparison = run(args.input, args.output_dir)
    print(f"Registros evaluables: {comparison[0]['evaluable_records']}")
    print(f"Reglas comparadas: {len(comparison)}")


if __name__ == "__main__":
    main()
