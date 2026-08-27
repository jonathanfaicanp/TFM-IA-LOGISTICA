"""Aggregate B30 relative deviations in 2026 by vehicle and distance range.

Baselines are built exclusively from valid 2024-2025 records. Individual
records are processed in memory and are never written to output files.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import median

from compare_baselines import RANGES, distance_range, number, parse_number, parse_start_date, percentile, write_csv


CONTEXT_MINIMUM = 30


def distribution(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {key: None for key in ("median", "p90", "p95")}
    return {
        "median": number(median(values)),
        "p90": number(percentile(values, 0.90)),
        "p95": number(percentile(values, 0.95)),
    }


def pct_above(values: list[float], threshold: float) -> float:
    return number(100 * sum(value > threshold for value in values) / len(values)) if values else 0.0


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
            record = {
                "vehicle": row["Codigo Vehiculo"],
                "range": distance_range(distance_km),
                "l_100km": consumption_liters / distance_km * 100,
            }
            if date.year == 2026:
                evaluation.append(record)
            else:
                history.append(record)
    return history, evaluation


def build_baselines(history: list[dict]) -> tuple[dict[str, float], dict[tuple[str, str], tuple[float, int]]]:
    by_vehicle: dict[str, list[float]] = defaultdict(list)
    by_context: dict[tuple[str, str], list[float]] = defaultdict(list)
    for record in history:
        by_vehicle[record["vehicle"]].append(record["l_100km"])
        by_context[(record["vehicle"], record["range"])].append(record["l_100km"])
    return (
        {vehicle: median(values) for vehicle, values in by_vehicle.items()},
        {key: (median(values), len(values)) for key, values in by_context.items()},
    )


def summary_row(label: str, values: list[float], label_name: str) -> dict:
    return {
        label_name: label,
        "registros_evaluables": len(values),
        "desviacion_mediana": distribution(values)["median"],
        "desviacion_p90": distribution(values)["p90"],
        "desviacion_p95": distribution(values)["p95"],
        "porcentaje_over_50pct": pct_above(values, 0.50),
        "porcentaje_over_100pct": pct_above(values, 1.00),
        "porcentaje_over_200pct": pct_above(values, 2.00),
        "porcentaje_over_500pct": pct_above(values, 5.00),
    }


def run(input_path: Path, output_dir: Path) -> tuple[list[dict], list[dict]]:
    history, evaluation = load_records(input_path)
    vehicle_baselines, context_baselines = build_baselines(history)
    per_vehicle: dict[str, list[float]] = defaultdict(list)
    per_range: dict[str, list[float]] = defaultdict(list)
    for record in evaluation:
        baseline = vehicle_baselines.get(record["vehicle"])
        contextual = context_baselines.get((record["vehicle"], record["range"]))
        if contextual is not None and contextual[1] >= CONTEXT_MINIMUM:
            baseline = contextual[0]
        if baseline is None:
            continue
        deviation = (record["l_100km"] - baseline) / baseline
        per_vehicle[record["vehicle"]].append(deviation)
        per_range[record["range"]].append(deviation)

    vehicle_rows = [summary_row(vehicle, values, "codigo_vehiculo") for vehicle, values in per_vehicle.items()]
    vehicle_rows.sort(key=lambda row: (-row["porcentaje_over_100pct"], -row["porcentaje_over_200pct"], int(row["codigo_vehiculo"])))
    range_rows = [summary_row(range_name, per_range[range_name], "rango_distancia_km") for range_name in RANGES]
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "b30_2026_vehicle_summary.csv", list(vehicle_rows[0]), vehicle_rows)
    write_csv(output_dir / "b30_2026_distance_summary.csv", list(range_rows[0]), range_rows)
    return vehicle_rows, range_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/datos_operativa.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    vehicles, ranges = run(args.input, args.output_dir)
    print(f"Vehiculos evaluados: {len(vehicles)}")
    print(f"Registros evaluables: {sum(row['registros_evaluables'] for row in vehicles)}")


if __name__ == "__main__":
    main()
