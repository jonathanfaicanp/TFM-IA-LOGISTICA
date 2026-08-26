"""Experimento reproducible: baseline global vs. baseline por distancia.

Lee el CSV de operativa sin modificarlo. Todas las selecciones se realizan en
memoria y las salidas contienen exclusivamente estadisticas agregadas.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Iterable


RANGES = (
    "<= 1",
    "> 1 y <= 2",
    "> 2 y <= 5",
    "> 5 y <= 10",
    "> 10 y <= 20",
    "> 20 y <= 50",
    "> 50 y <= 100",
    "> 100 y <= 300",
    "> 300",
)


def parse_number(value: str) -> float:
    """Parse Spanish decimal text, accepting a dot as thousands separator."""
    text = value.strip().replace("\u00a0", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    return float(text)


def parse_start_date(value: str) -> datetime:
    """Parse the ISO-like source date, including its millisecond suffix."""
    return datetime.fromisoformat(value.strip())


def distance_range(distance_km: float) -> str:
    if distance_km <= 1:
        return RANGES[0]
    if distance_km <= 2:
        return RANGES[1]
    if distance_km <= 5:
        return RANGES[2]
    if distance_km <= 10:
        return RANGES[3]
    if distance_km <= 20:
        return RANGES[4]
    if distance_km <= 50:
        return RANGES[5]
    if distance_km <= 100:
        return RANGES[6]
    if distance_km <= 300:
        return RANGES[7]
    return RANGES[8]


def percentile(values: Iterable[float], probability: float) -> float:
    """Linear-interpolated percentile, equivalent to pandas' default method."""
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Cannot calculate a percentile for no values")
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    return ordered[lower] + (position - lower) * (ordered[upper] - ordered[lower])


def number(value: float) -> float:
    """Round floating output for stable, readable aggregate files."""
    return round(value, 8)


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run(input_path: Path, output_dir: Path) -> dict:
    historical_rows = 0
    historical_vehicles: set[str] = set()
    valid: list[dict] = []

    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file, delimiter=";"):
            start = parse_start_date(row["Fecha de inicio"])
            # Convert this field too, even though the current experiment does not use it.
            _driving_indicator = parse_number(row["Indicador de conduccion"])
            if start.year not in (2024, 2025):
                continue
            historical_rows += 1
            vehicle = row["Codigo Vehiculo"]
            historical_vehicles.add(vehicle)
            distance_km = parse_number(row["Distancia"]) / 1000
            consumption_liters = parse_number(row["Consumo"]) / 1000
            if distance_km <= 0 or consumption_liters <= 0:
                continue
            valid.append(
                {
                    "vehicle": vehicle,
                    "distance_km": distance_km,
                    "consumption_liters": consumption_liters,
                    "l_100km": consumption_liters / distance_km * 100,
                    "range": distance_range(distance_km),
                }
            )

    counts_by_vehicle = Counter(record["vehicle"] for record in valid)
    eligible = {vehicle for vehicle, count in counts_by_vehicle.items() if count >= 100}
    covered = [record for record in valid if record["vehicle"] in eligible]
    by_vehicle: dict[str, list[float]] = defaultdict(list)
    by_context: dict[tuple[str, str], list[float]] = defaultdict(list)
    for record in covered:
        by_vehicle[record["vehicle"]].append(record["l_100km"])
        by_context[(record["vehicle"], record["range"])].append(record["l_100km"])

    vehicle_baselines = {vehicle: median(values) for vehicle, values in by_vehicle.items()}
    context_baselines = {key: median(values) for key, values in by_context.items()}
    vehicle_rows = []
    for vehicle in sorted(vehicle_baselines, key=lambda value: int(value)):
        values = by_vehicle[vehicle]
        vehicle_rows.append(
            {
                "codigo_vehiculo": vehicle,
                "registros_validos": len(values),
                "baseline_vehicle_l_100km": number(vehicle_baselines[vehicle]),
            }
        )

    context_rows = []
    for vehicle, range_name in sorted(by_context, key=lambda key: (int(key[0]), RANGES.index(key[1]))):
        values = by_context[(vehicle, range_name)]
        context_rows.append(
            {
                "codigo_vehiculo": vehicle,
                "rango_distancia_km": range_name,
                "registros": len(values),
                "baseline_contextual_l_100km": number(context_baselines[(vehicle, range_name)]),
            }
        )

    range_rows = []
    for range_name in RANGES:
        counts = [len(by_context[(vehicle, range_name)]) for vehicle in eligible if (vehicle, range_name) in by_context]
        range_rows.append(
            {
                "rango_distancia_km": range_name,
                "registros": sum(counts),
                "vehiculos_representados": len(counts),
                "mediana_observaciones_por_vehiculo": number(median(counts)) if counts else None,
                "p25_observaciones_por_vehiculo": number(percentile(counts, 0.25)) if counts else None,
                "p75_observaciones_por_vehiculo": number(percentile(counts, 0.75)) if counts else None,
            }
        )

    relative_a = [(record["l_100km"] - vehicle_baselines[record["vehicle"]]) / vehicle_baselines[record["vehicle"]] for record in covered]
    relative_b = [(record["l_100km"] - context_baselines[(record["vehicle"], record["range"])]) / context_baselines[(record["vehicle"], record["range"])] for record in covered]
    combinations = list(by_context.values())
    covered_count = len(covered)
    summary = {
        "scope": {
            "years": [2024, 2025],
            "validity_rule": "Consumo > 0 and Distancia > 0",
            "unit_conversions": {"distancia_km": "Distancia / 1000", "consumo_litros": "Consumo / 1000"},
            "kpi": "consumo_l_100km = consumo_litros / distancia_km * 100",
        },
        "historical_rows_2024_2025": historical_rows,
        "total_vehicles_2024_2025": len(historical_vehicles),
        "valid_records_2024_2025": len(valid),
        "vehicles_with_at_least_100_valid_records": len(eligible),
        "strategy_a": {
            "vehicles_with_baseline": len(vehicle_baselines),
            "records_covered": covered_count,
            "coverage_pct_of_valid_records": number(100 * covered_count / len(valid)) if valid else 0,
        },
        "strategy_b": {
            "vehicle_range_combinations": len(combinations),
            "combinations_at_least_5": sum(len(values) >= 5 for values in combinations),
            "combinations_at_least_10": sum(len(values) >= 10 for values in combinations),
            "combinations_at_least_20": sum(len(values) >= 20 for values in combinations),
            "combinations_at_least_30": sum(len(values) >= 30 for values in combinations),
            "combinations_at_least_50": sum(len(values) >= 50 for values in combinations),
            "combinations_less_than_5": sum(len(values) < 5 for values in combinations),
            "records_covered": covered_count,
            "coverage_pct_of_valid_records": number(100 * covered_count / len(valid)) if valid else 0,
        },
        "experimental_relative_deviation": {
            "note": "Descriptive only; no anomaly threshold or classification is applied.",
            "strategy_a": {"p25": number(percentile(relative_a, 0.25)), "median": number(median(relative_a)), "p75": number(percentile(relative_a, 0.75))},
            "strategy_b": {"p25": number(percentile(relative_b, 0.25)), "median": number(median(relative_b)), "p75": number(percentile(relative_b, 0.75))},
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "baseline_comparison_summary_2024_2025.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(output_dir / "baseline_vehicle_2024_2025.csv", list(vehicle_rows[0]), vehicle_rows)
    write_csv(output_dir / "baseline_contextual_2024_2025.csv", list(context_rows[0]), context_rows)
    write_csv(output_dir / "baseline_range_coverage_2024_2025.csv", list(range_rows[0]), range_rows)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/datos_operativa.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    summary = run(args.input, args.output_dir)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
