"""Explore historical feasibility of a duration-and-distance signal.

This is descriptive only: it does not classify trips, choose thresholds or
infer causes. All source-row calculations remain in memory and output is
restricted to aggregate statistics.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from compare_baselines import RANGES, distance_range, number, parse_number, parse_start_date, percentile, write_csv


YEARS = (2024, 2025, 2026)
CONTEXT_MINIMUM = 30
VEHICLE_MINIMUM = 100
QUANTILES = (("p25", .25), ("p75", .75), ("p90", .90), ("p95", .95), ("p99", .99))
OUTPUT_FIELDS = ("section", "variable", "year", "distance_range", "n", "value", "median", "p25", "p75", "p90", "p95", "p99")


def transform_duration_distance(duration_seconds: float, distance_meters: float) -> tuple[float, float, float]:
    distance_km = distance_meters / 1000
    duration_minutes = duration_seconds / 60
    return distance_km, duration_minutes, duration_minutes / distance_km


def summarize(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "median": None, **{name: None for name, _ in QUANTILES}}
    return {
        "n": len(values),
        "median": number(median(values)),
        **{name: number(percentile(values, probability)) for name, probability in QUANTILES},
    }


def absolute_median_change_pct(values_2024: list[float], values_2025: list[float]) -> float:
    earlier = median(values_2024)
    later = median(values_2025)
    return abs((later - earlier) / earlier) * 100


def load_valid_records(input_path: Path) -> list[dict]:
    records = []
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file, delimiter=";"):
            start = parse_start_date(row["Fecha de inicio"])
            if start.year not in YEARS:
                continue
            duration_seconds = parse_number(row["Duracion"])
            distance_meters = parse_number(row["Distancia"])
            if duration_seconds <= 0 or distance_meters <= 0:
                continue
            distance_km, duration_minutes, minutes_per_km = transform_duration_distance(duration_seconds, distance_meters)
            records.append({
                "vehicle": row["Codigo Vehiculo"],
                "year": start.year,
                "range": distance_range(distance_km),
                "duration_minutes": duration_minutes,
                "minutes_per_km": minutes_per_km,
            })
    return records


def analyze(records: list[dict]) -> tuple[dict, list[dict]]:
    by_year = Counter(record["year"] for record in records)
    by_range = Counter(record["range"] for record in records)
    historical = [record for record in records if record["year"] in (2024, 2025)]
    evaluation = [record for record in records if record["year"] == 2026]
    historical_contexts: dict[tuple[str, str], list[dict]] = defaultdict(list)
    historical_vehicles = Counter()
    yearly_contexts: dict[tuple[int, str, str], list[dict]] = defaultdict(list)
    for record in historical:
        historical_contexts[(record["vehicle"], record["range"])].append(record)
        historical_vehicles[record["vehicle"]] += 1
        yearly_contexts[(record["year"], record["vehicle"], record["range"])].append(record)

    eligible_contexts = {key for key, values in historical_contexts.items() if len(values) >= CONTEXT_MINIMUM}
    covered_2026 = sum((record["vehicle"], record["range"]) in eligible_contexts for record in evaluation)
    stable_keys = {
        (vehicle, range_name)
        for _, vehicle, range_name in yearly_contexts
        if len(yearly_contexts.get((2024, vehicle, range_name), ())) >= CONTEXT_MINIMUM
        and len(yearly_contexts.get((2025, vehicle, range_name), ())) >= CONTEXT_MINIMUM
    }
    changes = {variable: [] for variable in ("duration_minutes", "minutes_per_km")}
    for vehicle, range_name in stable_keys:
        for variable in changes:
            changes[variable].append(absolute_median_change_pct(
                [record[variable] for record in yearly_contexts[(2024, vehicle, range_name)]],
                [record[variable] for record in yearly_contexts[(2025, vehicle, range_name)]],
            ))

    context_counts = [len(values) for values in historical_contexts.values()]
    result = {
        "valid_records_total": len(records),
        "valid_records_by_year": {str(year): by_year[year] for year in YEARS},
        "vehicles_with_valid_records": len({record["vehicle"] for record in records}),
        "records_by_distance_range": {range_name: by_range[range_name] for range_name in RANGES},
        "historical_contexts": len(historical_contexts),
        "historical_context_observations": summarize(context_counts),
        "historical_contexts_ge_30": len(eligible_contexts),
        "valid_2026_records": len(evaluation),
        "valid_2026_records_context_ge_30": covered_2026,
        "valid_2026_context_coverage_pct": number(100 * covered_2026 / len(evaluation)) if evaluation else 0.0,
        "historical_vehicles_ge_100": sum(count >= VEHICLE_MINIMUM for count in historical_vehicles.values()),
        "contexts_ge_30_in_each_year": len(stable_keys),
        "absolute_median_change_pct_2024_2025": {variable: summarize(values) for variable, values in changes.items()},
    }

    rows = [
        {"section": "overall", "variable": "valid_records", "n": len(records), "value": len(records)},
        {"section": "overall", "variable": "vehicles_with_valid_records", "n": len({record["vehicle"] for record in records}), "value": len({record["vehicle"] for record in records})},
    ]
    rows.extend({"section": "valid_records_by_year", "year": year, "n": by_year[year], "value": by_year[year]} for year in YEARS)
    rows.extend({"section": "records_by_distance_range", "distance_range": name, "n": by_range[name], "value": by_range[name]} for name in RANGES)
    for range_name in RANGES:
        selected = [record for record in records if record["range"] == range_name]
        for variable in ("duration_minutes", "minutes_per_km"):
            rows.append({"section": "distribution_by_distance_range", "variable": variable, "distance_range": range_name, **summarize([record[variable] for record in selected])})
    rows.append({"section": "historical_contexts", "variable": "observation_count", "value": len(historical_contexts), **summarize(context_counts)})
    rows.append({"section": "historical_contexts", "variable": "contexts_ge_30", "n": len(eligible_contexts), "value": len(eligible_contexts)})
    rows.append({"section": "context_coverage_2026", "variable": "records_context_ge_30", "n": len(evaluation), "value": number(100 * covered_2026 / len(evaluation)) if evaluation else 0.0})
    rows.append({"section": "historical_vehicles", "variable": "vehicles_ge_100", "n": len(historical_vehicles), "value": sum(count >= VEHICLE_MINIMUM for count in historical_vehicles.values())})
    for variable, values in changes.items():
        rows.append({"section": "absolute_median_change_pct_2024_2025", "variable": variable, "value": len(stable_keys), **summarize(values)})
    normalized_rows = [{field: row.get(field) for field in OUTPUT_FIELDS} for row in rows]
    return result, normalized_rows


def run(input_path: Path, output_path: Path) -> dict:
    result, rows = analyze(load_valid_records(input_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output_path, list(OUTPUT_FIELDS), rows)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/datos_operativa.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/duration_distance_feasibility_summary.csv"))
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
