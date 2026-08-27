"""Sensitivity analysis of minimum evaluated distance using the fixed B30 baseline.

Baselines are built from valid 2024-2025 data only. 2026 records are handled
in memory; output files contain aggregate scenario and range statistics only.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import median

from compare_baselines import RANGES, distance_range, number, parse_number, parse_start_date, percentile, write_csv


SCENARIOS = (("sin_filtro", None), ("distancia_gt_0_5km", 0.5), ("distancia_gt_1km", 1.0), ("distancia_gt_2km", 2.0), ("distancia_gt_5km", 5.0))
CONTEXT_MINIMUM = 30


def dist(values: list[float], quantiles: tuple[float, ...]) -> dict[str, float | None]:
    if not values:
        return {f"p{int(q * 100)}": None for q in quantiles}
    return {f"p{int(q * 100)}": number(percentile(values, q)) for q in quantiles}


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
            record = {"vehicle": row["Codigo Vehiculo"], "distance_km": distance_km, "range": distance_range(distance_km), "l_100km": consumption_liters / distance_km * 100}
            if date.year == 2026:
                evaluation.append(record)
            else:
                history.append(record)
    return history, evaluation


def build_baselines(history: list[dict]) -> tuple[dict[str, float], dict[tuple[str, str], tuple[float, int]]]:
    vehicles: dict[str, list[float]] = defaultdict(list)
    contexts: dict[tuple[str, str], list[float]] = defaultdict(list)
    for record in history:
        vehicles[record["vehicle"]].append(record["l_100km"])
        contexts[(record["vehicle"], record["range"])].append(record["l_100km"])
    return ({key: median(values) for key, values in vehicles.items()}, {key: (median(values), len(values)) for key, values in contexts.items()})


def b30_deviation(record: dict, vehicles: dict[str, float], contexts: dict[tuple[str, str], tuple[float, int]]) -> float | None:
    baseline = vehicles.get(record["vehicle"])
    contextual = contexts.get((record["vehicle"], record["range"]))
    if contextual is not None and contextual[1] >= CONTEXT_MINIMUM:
        baseline = contextual[0]
    return None if baseline is None else (record["l_100km"] - baseline) / baseline


def scenario_summary(name: str, minimum_km: float | None, valid: list[dict], vehicles: dict[str, float], contexts: dict[tuple[str, str], tuple[float, int]]) -> tuple[dict, list[dict]]:
    selected = valid if minimum_km is None else [record for record in valid if record["distance_km"] > minimum_km]
    evaluated: list[tuple[dict, float]] = []
    for record in selected:
        deviation = b30_deviation(record, vehicles, contexts)
        if deviation is not None:
            evaluated.append((record, deviation))
    l100 = [record["l_100km"] for record, _ in evaluated]
    deviations = [deviation for _, deviation in evaluated]
    counts = {threshold: sum(value > threshold for value in deviations) for threshold in (.5, 1, 2, 5)}
    summary = {
        "scenario": name, "minimum_distance_km_strict": minimum_km,
        "valid_records_initial": len(valid), "records_after_distance_filter": len(selected),
        "records_discarded_by_filter": len(valid) - len(selected), "records_discarded_pct": pct(len(valid) - len(selected), len(valid)),
        "records_evaluable_b30": len(evaluated), "vehicles_evaluated": len({record["vehicle"] for record, _ in evaluated}),
        "l100_median": number(median(l100)) if l100 else None, **{f"l100_{key}": value for key, value in dist(l100, (.95, .99)).items()}, "l100_max": number(max(l100)) if l100 else None,
        "deviation_median": number(median(deviations)) if deviations else None, **{f"deviation_{key}": value for key, value in dist(deviations, (.75, .90, .95, .99)).items()},
    }
    for threshold, count in counts.items():
        label = f"over_{int(threshold * 100)}pct"
        summary[label] = count
        summary[f"{label}_pct"] = pct(count, len(evaluated))
    range_rows = []
    for range_name in RANGES:
        range_rows.append({"scenario": name, "minimum_distance_km_strict": minimum_km, "rango_distancia_km": range_name, "registros_despues_del_filtro": sum(record["range"] == range_name for record in selected), "registros_evaluables_b30": sum(record["range"] == range_name for record, _ in evaluated)})
    return summary, range_rows


def run(input_path: Path, output_dir: Path) -> tuple[list[dict], list[dict]]:
    history, valid = load_records(input_path)
    vehicles, contexts = build_baselines(history)
    summaries, ranges = [], []
    for name, minimum in SCENARIOS:
        summary, rows = scenario_summary(name, minimum, valid, vehicles, contexts)
        summaries.append(summary); ranges.extend(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "distance_threshold_sensitivity_2026.csv", list(summaries[0]), summaries)
    write_csv(output_dir / "distance_threshold_sensitivity_by_range_2026.csv", list(ranges[0]), ranges)
    return summaries, ranges


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/datos_operativa.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    summaries, _ = run(args.input, args.output_dir)
    for summary in summaries:
        print(f"{summary['scenario']}: {summary['records_evaluable_b30']} evaluables")


if __name__ == "__main__":
    main()
