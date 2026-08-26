"""Evaluacion temporal 2024->2025 de A, B30 y B50.

El CSV se lee sin modificarlo. Se generan solo tablas agregadas: nunca se
escriben viajes individuales ni desviaciones por registro.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import median

from compare_baselines import RANGES, distance_range, parse_number, parse_start_date, percentile, number, write_csv


STRATEGIES = {"A": None, "B30": 30, "B50": 50}


def load_records(input_path: Path) -> tuple[list[dict], list[dict]]:
    """Return valid 2024 construction records and valid 2025 evaluation records."""
    construction, evaluation = [], []
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file, delimiter=";"):
            start = parse_start_date(row["Fecha de inicio"])
            # Validate conversion of this source field although it is not a feature here.
            _driving_indicator = parse_number(row["Indicador de conduccion"])
            if start.year not in (2024, 2025):
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
            (construction if start.year == 2024 else evaluation).append(record)
    return construction, evaluation


def build_baselines(construction: list[dict]) -> tuple[dict[str, float], dict[tuple[str, str], tuple[float, int]]]:
    by_vehicle: dict[str, list[float]] = defaultdict(list)
    by_context: dict[tuple[str, str], list[float]] = defaultdict(list)
    for record in construction:
        by_vehicle[record["vehicle"]].append(record["l_100km"])
        by_context[(record["vehicle"], record["range"])].append(record["l_100km"])
    vehicle = {key: median(values) for key, values in by_vehicle.items()}
    context = {key: (median(values), len(values)) for key, values in by_context.items()}
    return vehicle, context


def distribution(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {key: None for key in ("median", "p75", "p90", "p95", "p99")}
    return {
        "median": number(median(values)),
        "p75": number(percentile(values, 0.75)),
        "p90": number(percentile(values, 0.90)),
        "p95": number(percentile(values, 0.95)),
        "p99": number(percentile(values, 0.99)),
    }


def evaluate_strategy(
    name: str,
    minimum_context: int | None,
    evaluation: list[dict],
    vehicle_baselines: dict[str, float],
    context_baselines: dict[tuple[str, str], tuple[float, int]],
) -> tuple[dict, list[dict]]:
    deviations: list[float] = []
    by_range: dict[str, dict[str, object]] = defaultdict(lambda: {"evaluated": 0, "without": 0, "contextual": 0, "fallback": 0, "deviations": []})
    evaluated_vehicles: set[str] = set()
    fallback_vehicles: set[str] = set()
    contextual_evaluations = fallback_evaluations = without_baseline = 0

    for record in evaluation:
        vehicle, range_name = record["vehicle"], record["range"]
        baseline = vehicle_baselines.get(vehicle)
        source = "vehicle"
        context = context_baselines.get((vehicle, range_name))
        if minimum_context is not None and context is not None and context[1] >= minimum_context:
            baseline, source = context[0], "contextual"
        if baseline is None:
            without_baseline += 1
            by_range[range_name]["without"] += 1
            continue
        relative_deviation = (record["l_100km"] - baseline) / baseline
        deviations.append(relative_deviation)
        evaluated_vehicles.add(vehicle)
        by_range[range_name]["evaluated"] += 1
        by_range[range_name]["deviations"].append(relative_deviation)
        if source == "contextual":
            contextual_evaluations += 1
            by_range[range_name]["contextual"] += 1
        else:
            if minimum_context is not None:
                fallback_evaluations += 1
                fallback_vehicles.add(vehicle)
                by_range[range_name]["fallback"] += 1

    evaluable = len(deviations)
    range_rows = []
    for range_name in RANGES:
        stats = by_range[range_name]
        range_rows.append(
            {
                "strategy": name,
                "rango_distancia_km": range_name,
                "registros_evaluables": stats["evaluated"],
                "registros_sin_baseline": stats["without"],
                "uso_contextual": stats["contextual"],
                "uso_fallback": stats["fallback"],
                **{f"desviacion_{key}": value for key, value in distribution(stats["deviations"]).items()},
            }
        )
    summary = {
        "strategy": name,
        "context_minimum_records": minimum_context,
        "evaluation_records_total": len(evaluation),
        "evaluable_records": evaluable,
        "records_without_baseline": without_baseline,
        "coverage_pct": number(100 * evaluable / len(evaluation)) if evaluation else 0,
        "evaluated_vehicles": len(evaluated_vehicles),
        "vehicles_with_fallback": len(fallback_vehicles),
        "contextual_evaluations": contextual_evaluations,
        "fallback_evaluations": fallback_evaluations,
        "contextual_evaluations_pct": number(100 * contextual_evaluations / evaluable) if evaluable else 0,
        "fallback_evaluations_pct": number(100 * fallback_evaluations / evaluable) if evaluable else 0,
        "relative_deviation": distribution(deviations),
        "positive_deviation_counts": {
            "over_25pct": sum(value > 0.25 for value in deviations),
            "over_50pct": sum(value > 0.50 for value in deviations),
            "over_100pct": sum(value > 1.00 for value in deviations),
            "over_200pct": sum(value > 2.00 for value in deviations),
        },
    }
    return summary, range_rows


def run(input_path: Path, output_dir: Path) -> dict:
    construction, evaluation = load_records(input_path)
    vehicle_baselines, context_baselines = build_baselines(construction)
    summaries, range_rows = [], []
    for name, minimum_context in STRATEGIES.items():
        summary, rows = evaluate_strategy(name, minimum_context, evaluation, vehicle_baselines, context_baselines)
        summaries.append(summary)
        range_rows.extend(rows)
    result = {
        "construction_year": 2024,
        "evaluation_year": 2025,
        "construction_valid_records": len(construction),
        "construction_vehicles_with_vehicle_baseline": len(vehicle_baselines),
        "construction_vehicle_range_groups": len(context_baselines),
        "evaluation_valid_records": len(evaluation),
        "strategies": summaries,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "baseline_strategy_evaluation_summary_2025.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary_rows = []
    for summary in summaries:
        row = {key: value for key, value in summary.items() if key not in ("relative_deviation", "positive_deviation_counts")}
        row.update({f"desviacion_{key}": value for key, value in summary["relative_deviation"].items()})
        row.update(summary["positive_deviation_counts"])
        summary_rows.append(row)
    write_csv(output_dir / "baseline_strategy_evaluation_summary_2025.csv", list(summary_rows[0]), summary_rows)
    write_csv(output_dir / "baseline_strategy_evaluation_by_range_2025.csv", list(range_rows[0]), range_rows)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/datos_operativa.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
