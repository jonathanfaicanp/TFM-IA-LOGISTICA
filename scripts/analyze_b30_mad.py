"""Robust-MAD experiment for B30, with 2024-2025 construction and 2026 evaluation.

All record-level calculations stay in memory.  Outputs are aggregate summaries
only and robust-z values are descriptive, never anomaly classifications.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import median

from compare_baselines import RANGES, distance_range, number, parse_number, parse_start_date, percentile, write_csv


CONTEXT_MINIMUM = 30
MAD_SCALE = 1.4826


def median_mad(values: list[float]) -> tuple[float, float, float]:
    """Return median, MAD and 1.4826-scaled MAD for a non-empty sample."""
    centre = median(values)
    mad = median([abs(value - centre) for value in values])
    return centre, mad, MAD_SCALE * mad


def robust_z(value: float, centre: float, scale: float) -> float | None:
    return None if scale == 0 else (value - centre) / scale


def distribution(values: list[float], labels: tuple[tuple[str, float], ...]) -> dict[str, float | None]:
    if not values:
        return {label: None for label, _ in labels}
    return {label: number(percentile(values, probability)) for label, probability in labels}


def pct(count: int, total: int) -> float:
    return number(100 * count / total) if total else 0.0


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
            record = {"vehicle": row["Codigo Vehiculo"], "range": distance_range(distance_km), "l_100km": consumption_liters / distance_km * 100}
            (evaluation if date.year == 2026 else history).append(record)
    return history, evaluation


def build_scopes(history: list[dict]) -> tuple[dict[str, tuple[float, float, float]], dict[tuple[str, str], tuple[float, float, float, int]]]:
    by_vehicle: dict[str, list[float]] = defaultdict(list)
    by_context: dict[tuple[str, str], list[float]] = defaultdict(list)
    for record in history:
        by_vehicle[record["vehicle"]].append(record["l_100km"])
        by_context[(record["vehicle"], record["range"])].append(record["l_100km"])
    vehicles = {vehicle: median_mad(values) for vehicle, values in by_vehicle.items()}
    contexts = {key: (*median_mad(values), len(values)) for key, values in by_context.items()}
    return vehicles, contexts


def select_b30_scope(record: dict, vehicles: dict, contexts: dict) -> tuple[float, float, float, str] | None:
    contextual = contexts.get((record["vehicle"], record["range"]))
    if contextual is not None and contextual[3] >= CONTEXT_MINIMUM:
        return contextual[:3] + ("contextual",)
    vehicle = vehicles.get(record["vehicle"])
    return None if vehicle is None else vehicle + ("fallback",)


def score_summary(scores: list[float]) -> dict:
    summary = distribution(scores, (("median", .5), ("p75", .75), ("p90", .9), ("p95", .95), ("p99", .99)))
    summary["max"] = number(max(scores)) if scores else None
    summary["negative_count"] = sum(score < 0 for score in scores)
    summary["zero_count"] = sum(score == 0 for score in scores)
    summary["positive_count"] = sum(score > 0 for score in scores)
    for threshold in (1, 2, 3, 4, 5):
        count = sum(score > threshold for score in scores)
        summary[f"over_{threshold}"] = count
        summary[f"over_{threshold}_pct_of_scored"] = pct(count, len(scores))
    return summary


def relative_summary(values: list[float]) -> dict:
    return distribution(values, (("median", .5), ("p75", .75), ("p90", .9), ("p95", .95), ("p99", .99)))


def run(input_path: Path, output_dir: Path) -> dict:
    history, evaluation = load_records(input_path)
    vehicles, contexts = build_scopes(history)
    scores: list[float] = []
    relative: list[float] = []
    mad_zero = no_baseline = 0
    by_range: dict[str, dict[str, list | int]] = defaultdict(lambda: {"evaluated": 0, "mad_zero": 0, "scores": []})
    by_vehicle: dict[str, dict[str, list | int]] = defaultdict(lambda: {"evaluated": 0, "mad_zero": 0, "scores": []})
    for record in evaluation:
        scope = select_b30_scope(record, vehicles, contexts)
        if scope is None:
            no_baseline += 1
            continue
        centre, _, scale, _ = scope
        rel = (record["l_100km"] - centre) / centre
        relative.append(rel)
        for group in (by_range[record["range"]], by_vehicle[record["vehicle"]]):
            group["evaluated"] += 1
        score = robust_z(record["l_100km"], centre, scale)
        if score is None:
            mad_zero += 1
            by_range[record["range"]]["mad_zero"] += 1
            by_vehicle[record["vehicle"]]["mad_zero"] += 1
            continue
        scores.append(score)
        by_range[record["range"]]["scores"].append(score)
        by_vehicle[record["vehicle"]]["scores"].append(score)

    range_rows = []
    for range_name in RANGES:
        group = by_range[range_name]
        s = group["scores"]
        range_rows.append({"rango_distancia_km": range_name, "registros_evaluables": group["evaluated"], "registros_mad_zero": group["mad_zero"], "registros_con_robust_z": len(s), "robust_z_mediana": distribution(s, (("median", .5),))["median"], "robust_z_p95": distribution(s, (("p95", .95),))["p95"], **{f"porcentaje_robust_z_over_{threshold}": pct(sum(score > threshold for score in s), len(s)) for threshold in (2, 3, 4, 5)}})
    vehicle_rows = []
    for vehicle_id, group in sorted(by_vehicle.items(), key=lambda item: int(item[0])):
        s = group["scores"]
        vehicle_rows.append({"codigo_vehiculo": vehicle_id, "registros_evaluables": group["evaluated"], "registros_mad_zero": group["mad_zero"], "registros_con_robust_z": len(s), "robust_z_mediana": distribution(s, (("median", .5),))["median"], "robust_z_p95": distribution(s, (("p95", .95),))["p95"], "porcentaje_robust_z_over_3": pct(sum(score > 3 for score in s), len(s)), "porcentaje_robust_z_over_5": pct(sum(score > 5 for score in s), len(s))})
    result = {"construction_years": [2024, 2025], "evaluation_year": 2026, "history_valid_records": len(history), "evaluation_valid_records": len(evaluation), "records_evaluable": len(relative), "records_without_baseline": no_baseline, "records_mad_zero": mad_zero, "records_with_robust_z": len(scores), "relative_deviation": relative_summary(relative), "robust_z": score_summary(scores)}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "b30_mad_2026_summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(output_dir / "b30_mad_2026_distance_summary.csv", list(range_rows[0]), range_rows)
    write_csv(output_dir / "b30_mad_2026_vehicle_summary.csv", list(vehicle_rows[0]), vehicle_rows)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/datos_operativa.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
