"""Semi-synthetic benchmark of B30/MAD candidate rules on controlled perturbations.

Historical scopes come only from 2024-2025.  2026 controls and perturbed
versions are calculated in memory; output files contain aggregate metrics only.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from analyze_b30_mad import build_scopes, robust_z, select_b30_scope
from compare_baselines import RANGES, distance_range, number, parse_number, parse_start_date, write_csv
from evaluate_detector_candidates import relative_deviation, rule_and, rule_or


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
SCOPES = (("completo", lambda record: True), ("distancia_lte_1km", lambda record: record["distance_km"] <= 1), ("distancia_gt_5km", lambda record: record["distance_km"] > 5), ("distancia_gt_20km", lambda record: record["distance_km"] > 20))


def perturb_consumption(consumption_liters: float, perturbation: float) -> float:
    return consumption_liters * (1 + perturbation)


def perturbed_l100(consumption_liters: float, distance_km: float, perturbation: float) -> float:
    return perturb_consumption(consumption_liters, perturbation) / distance_km * 100


def perturb_record(record: dict, perturbation: float) -> dict:
    """Return an in-memory perturbed copy, leaving the source record untouched."""
    perturbed_consumption = perturb_consumption(record["consumption_liters"], perturbation)
    return {
        **record,
        "consumption_liters": perturbed_consumption,
        "l_100km": perturbed_consumption / record["distance_km"] * 100,
    }


def apply_rule(relative: float, score: float | None, family: str, first: float, second: float | None, operation: str | None) -> bool:
    if family == "D1":
        return relative > first
    if score is None:
        return False
    if family == "D2":
        return score > first
    return rule_and(relative, score, first, second) if operation == "AND" else rule_or(relative, score, first, second)


def rates(positives: int, true_positives: int, negatives: int, false_positives: int) -> dict[str, float | int]:
    recall = 100 * true_positives / positives if positives else 0.0
    fpr = 100 * false_positives / negatives if negatives else 0.0
    return {"cases_perturbed_evaluable": positives, "detected": true_positives, "recall_pct": number(recall), "false_negatives": positives - true_positives, "false_negative_rate_pct": number(100 - recall) if positives else 0.0, "control_cases": negatives, "false_positives": false_positives, "false_positive_rate_pct": number(fpr), "specificity_pct": number(100 - fpr) if negatives else 0.0}


def load_records(input_path: Path) -> tuple[list[dict], list[dict]]:
    history, evaluation = [], []
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file, delimiter=";"):
            date = parse_start_date(row["Fecha de inicio"])
            if date.year not in (2024, 2025, 2026):
                continue
            distance_km = parse_number(row["Distancia"]) / 1000
            consumption_liters = parse_number(row["Consumo"]) / 1000
            if distance_km <= 0 or consumption_liters <= 0:
                continue
            record = {"vehicle": row["Codigo Vehiculo"], "range": distance_range(distance_km), "distance_km": distance_km, "consumption_liters": consumption_liters, "l_100km": consumption_liters / distance_km * 100}
            (evaluation if date.year == 2026 else history).append(record)
    return history, evaluation


def prepare_evaluation(history: list[dict], evaluation: list[dict]) -> list[dict]:
    compact_history = [{key: record[key] for key in ("vehicle", "range", "l_100km")} for record in history]
    vehicles, contexts = build_scopes(compact_history)
    prepared = []
    for record in evaluation:
        scope = select_b30_scope(record, vehicles, contexts)
        if scope is None:
            continue
        centre, _, scale, _ = scope
        prepared.append({**record, "centre": centre, "scale": scale})
    return prepared


def applicable(records: list[dict], family: str) -> list[dict]:
    return records if family == "D1" else [record for record in records if record["scale"] != 0]


def evaluate_group(records: list[dict], perturbation: float, rule: tuple) -> dict:
    _, family, first, second, operation = rule
    controls = [apply_rule(relative_deviation(record["l_100km"], record["centre"]), robust_z(record["l_100km"], record["centre"], record["scale"]), family, first, second, operation) for record in records]
    perturbed_records = [perturb_record(record, perturbation) for record in records]
    perturbed = [apply_rule(relative_deviation(record["l_100km"], record["centre"]), robust_z(record["l_100km"], record["centre"], record["scale"]), family, first, second, operation) for record in perturbed_records]
    return rates(len(records), sum(perturbed), len(records), sum(controls))


def run(input_path: Path, output_dir: Path) -> tuple[list[dict], list[dict]]:
    history, evaluation = load_records(input_path)
    prepared = prepare_evaluation(history, evaluation)
    summary_rows, range_rows = [], []
    for perturbation in PERTURBATIONS:
        for rule in RULES:
            name, family, first, second, operation = rule
            for scope_name, predicate in SCOPES:
                records = applicable([record for record in prepared if predicate(record)], family)
                summary_rows.append({"perturbation_pct": int(perturbation * 100), "scenario": name, "family": family, "scope": scope_name, "relative_threshold": first if family != "D2" else None, "robust_z_threshold": first if family == "D2" else second, "operation": operation, **evaluate_group(records, perturbation, rule)})
            for range_name in RANGES:
                records = applicable([record for record in prepared if record["range"] == range_name], family)
                range_rows.append({"perturbation_pct": int(perturbation * 100), "scenario": name, "family": family, "rango_distancia_km": range_name, **evaluate_group(records, perturbation, rule)})
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "synthetic_benchmark_summary.csv", list(summary_rows[0]), summary_rows)
    write_csv(output_dir / "synthetic_benchmark_by_range.csv", list(range_rows[0]), range_rows)
    return summary_rows, range_rows


def build_rule_comparison(summary_path: Path, output_path: Path) -> list[dict]:
    """Pivot existing complete-scope aggregates without rerunning the benchmark."""
    with summary_path.open("r", encoding="utf-8-sig", newline="") as file:
        complete = [row for row in csv.DictReader(file) if row["scope"] == "completo"]

    expected_levels = {int(level * 100) for level in PERTURBATIONS}
    by_scenario = {name: [] for name, *_ in RULES}
    for row in complete:
        if row["scenario"] in by_scenario:
            by_scenario[row["scenario"]].append(row)

    comparison = []
    for name, family, relative_threshold, robust_threshold, operation in RULES:
        rows = by_scenario[name]
        levels = {int(row["perturbation_pct"]) for row in rows}
        if levels != expected_levels:
            raise ValueError(f"Missing or duplicate perturbation levels for {name}")
        control_rates = {float(row["false_positive_rate_pct"]) for row in rows}
        if len(control_rates) != 1:
            raise ValueError(f"Control marked rate is not stable for {name}")
        control_marked = control_rates.pop()
        specificity = 100 - control_marked
        result = {
            "scenario": name,
            "family": family,
            "relative_threshold": relative_threshold if family != "D2" else None,
            "robust_z_threshold": relative_threshold if family == "D2" else robust_threshold,
            "operation": operation,
            "control_marked_pct_experimental": number(control_marked),
            "specificity_pct_experimental": number(specificity),
        }
        for row in sorted(rows, key=lambda item: int(item["perturbation_pct"])):
            level = int(row["perturbation_pct"])
            recall = float(row["recall_pct"])
            result[f"recall_pct_plus_{level}"] = number(recall)
            result[f"false_negative_rate_pct_plus_{level}"] = number(float(row["false_negative_rate_pct"]))
            result[f"balanced_accuracy_pct_plus_{level}"] = number((recall + specificity) / 2)
            result[f"youden_j_pct_points_plus_{level}"] = number(recall + specificity - 100)
        comparison.append(result)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output_path, list(comparison[0]), comparison)
    return comparison


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/datos_operativa.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--comparison-only", action="store_true", help="Build only the rule comparison from the existing summary CSV")
    args = parser.parse_args()
    if args.comparison_only:
        rows = build_rule_comparison(args.output_dir / "synthetic_benchmark_summary.csv", args.output_dir / "synthetic_benchmark_rule_comparison.csv")
        print(f"Reglas comparadas: {len(rows)}")
        return
    summaries, _ = run(args.input, args.output_dir)
    print(f"Filas agregadas de resumen: {len(summaries)}")


if __name__ == "__main__":
    main()
