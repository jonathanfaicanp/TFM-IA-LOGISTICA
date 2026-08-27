"""Evaluate vehicle and distance-context baselines on 2026 without leakage.

Baselines use valid 2024-2025 records only. Outputs contain aggregates only;
neither the source CSV nor individual evaluation records are written.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import median

from compare_baselines import RANGES, distance_range, number, parse_number, parse_start_date, percentile, write_csv


STRATEGIES = {"A": None, "B30": 30, "B50": 50}


def load_data(input_path: Path) -> tuple[list[dict], list[dict], int]:
    """Return valid construction records, valid 2026 records, and 2026 row count."""
    history, evaluation, total_2026 = [], [], 0
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file, delimiter=";"):
            date = parse_start_date(row["Fecha de inicio"])
            # Validate the source conversion even though this field is not used as a feature.
            _driving_indicator = parse_number(row["Indicador de conduccion"])
            if date.year not in (2024, 2025, 2026):
                continue
            if date.year == 2026:
                total_2026 += 1
            distance_km = parse_number(row["Distancia"]) / 1000
            consumption_liters = parse_number(row["Consumo"]) / 1000
            if distance_km <= 0 or consumption_liters <= 0:
                continue
            record = {
                "vehicle": row["Codigo Vehiculo"],
                "range": distance_range(distance_km),
                "l_100km": consumption_liters / distance_km * 100,
            }
            if date.year in (2024, 2025):
                history.append(record)
            elif date.year == 2026:
                evaluation.append(record)
    return history, evaluation, total_2026


def build_baselines(history: list[dict]) -> tuple[dict[str, float], dict[tuple[str, str], tuple[float, int]]]:
    vehicles: dict[str, list[float]] = defaultdict(list)
    contexts: dict[tuple[str, str], list[float]] = defaultdict(list)
    for record in history:
        vehicles[record["vehicle"]].append(record["l_100km"])
        contexts[(record["vehicle"], record["range"])].append(record["l_100km"])
    return (
        {vehicle: median(values) for vehicle, values in vehicles.items()},
        {key: (median(values), len(values)) for key, values in contexts.items()},
    )


def distribution(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {name: None for name in ("median", "p75", "p90", "p95", "p99")}
    return {"median": number(median(values)), "p75": number(percentile(values, .75)), "p90": number(percentile(values, .90)), "p95": number(percentile(values, .95)), "p99": number(percentile(values, .99))}


def percentage(numerator: int, denominator: int) -> float:
    return number(100 * numerator / denominator) if denominator else 0.0


def evaluate(name: str, minimum_context: int | None, evaluation: list[dict], vehicle: dict[str, float], context: dict[tuple[str, str], tuple[float, int]]) -> tuple[dict, list[dict], list[dict]]:
    deviations: list[float] = []
    per_range: dict[str, list[float]] = defaultdict(list)
    per_vehicle: dict[str, list[float]] = defaultdict(list)
    contextual = fallback = missing = 0

    for record in evaluation:
        baseline, baseline_type = vehicle.get(record["vehicle"]), "vehicle"
        candidate = context.get((record["vehicle"], record["range"]))
        if minimum_context is not None and candidate is not None and candidate[1] >= minimum_context:
            baseline, baseline_type = candidate[0], "contextual"
        elif minimum_context is not None and baseline is not None:
            baseline_type = "fallback"
        if baseline is None:
            missing += 1
            continue
        deviation = (record["l_100km"] - baseline) / baseline
        deviations.append(deviation)
        per_range[record["range"]].append(deviation)
        per_vehicle[record["vehicle"]].append(deviation)
        contextual += baseline_type == "contextual"
        fallback += baseline_type == "fallback"

    evaluable = len(deviations)
    positive = {f"over_{threshold}pct": sum(value > threshold / 100 for value in deviations) for threshold in (25, 50, 100, 200, 500)}
    summary = {
        "strategy": name, "context_minimum_records": minimum_context,
        # Replaced with the unfiltered 2026 row count by run().
        "records_2026_total": len(evaluation),
        "records_2026_valid": len(evaluation), "records_evaluable": evaluable,
        "records_without_baseline": missing, "coverage_pct": percentage(evaluable, len(evaluation)),
        "vehicles_evaluated": len(per_vehicle), "contextual_evaluations_pct": percentage(contextual, evaluable),
        "fallback_evaluations_pct": percentage(fallback, evaluable), **{f"deviation_{key}": value for key, value in distribution(deviations).items()},
        **positive, **{f"{key}_pct": percentage(value, evaluable) for key, value in positive.items()},
        "vehicles_over_20pct_records_over_100pct": sum(percentage(sum(value > 1 for value in values), len(values)) > 20 for values in per_vehicle.values()),
    }
    range_rows = []
    for range_name in RANGES:
        values = per_range[range_name]
        range_rows.append({"strategy": name, "rango_distancia_km": range_name, "registros_evaluables": len(values), "desviacion_mediana": distribution(values)["median"], "desviacion_p95": distribution(values)["p95"], "porcentaje_over_50pct": percentage(sum(value > .5 for value in values), len(values)), "porcentaje_over_100pct": percentage(sum(value > 1 for value in values), len(values)), "porcentaje_over_200pct": percentage(sum(value > 2 for value in values), len(values))})
    vehicle_rows = []
    for vehicle_id, values in sorted(per_vehicle.items(), key=lambda item: int(item[0])):
        vehicle_rows.append({"strategy": name, "codigo_vehiculo": vehicle_id, "registros_evaluables": len(values), "desviacion_mediana": distribution(values)["median"], "desviacion_p95": distribution(values)["p95"], "porcentaje_over_100pct": percentage(sum(value > 1 for value in values), len(values))})
    return summary, range_rows, vehicle_rows


def run(input_path: Path, output_dir: Path) -> dict:
    history, evaluation, total_2026 = load_data(input_path)
    vehicle, context = build_baselines(history)
    summaries, range_rows, vehicle_rows = [], [], []
    for name, minimum in STRATEGIES.items():
        summary, ranges, vehicles = evaluate(name, minimum, evaluation, vehicle, context)
        summary["records_2026_total"] = total_2026
        summaries.append(summary); range_rows.extend(ranges); vehicle_rows.extend(vehicles)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = {"construction_years": [2024, 2025], "history_valid_records": len(history), "history_vehicle_baselines": len(vehicle), "history_context_groups": len(context), "records_2026_total": total_2026, "records_2026_valid": len(evaluation), "strategies": summaries}
    (output_dir / "baseline_2026_evaluation_summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(output_dir / "baseline_2026_evaluation_summary.csv", list(summaries[0]), summaries)
    write_csv(output_dir / "baseline_2026_evaluation_by_range.csv", list(range_rows[0]), range_rows)
    write_csv(output_dir / "baseline_2026_evaluation_by_vehicle.csv", list(vehicle_rows[0]), vehicle_rows)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/datos_operativa.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
