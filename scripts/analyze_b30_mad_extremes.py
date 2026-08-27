"""Describe aggregate characteristics of extreme B30 robust-z groups in 2026.

The B30/MAD construction uses 2024-2025 only. No individual source row or
score is saved; files contain aggregate group and distance-range summaries.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from pathlib import Path
from statistics import median

from analyze_b30_mad import build_scopes, robust_z, select_b30_scope
from compare_baselines import RANGES, distance_range, number, parse_number, parse_start_date, percentile, write_csv


THRESHOLDS = (3, 5, 10, 20, 50)


def q25_50_75(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"p25": None, "median": None, "p75": None}
    return {"p25": number(percentile(values, .25)), "median": number(median(values)), "p75": number(percentile(values, .75))}


def minimal_vehicles_for_half(records: list[dict]) -> int:
    """Smallest number of vehicles whose records account for at least half."""
    if not records:
        return 0
    cumulative = 0
    target = len(records) / 2
    for position, count in enumerate(sorted(Counter(record["vehicle"] for record in records).values(), reverse=True), start=1):
        cumulative += count
        if cumulative >= target:
            return position
    raise RuntimeError("unreachable")


def load_records(input_path: Path) -> tuple[list[dict], list[dict]]:
    history, evaluation = [], []
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file, delimiter=";"):
            date = parse_start_date(row["Fecha de inicio"])
            if date.year not in (2024, 2025, 2026):
                continue
            distance_m = parse_number(row["Distancia"])
            consumption_raw = parse_number(row["Consumo"])
            if distance_m <= 0 or consumption_raw <= 0:
                continue
            record = {
                "vehicle": row["Codigo Vehiculo"],
                "range": distance_range(distance_m / 1000),
                "distance_m": distance_m,
                "consumption_liters": consumption_raw / 1000,
                "duration_s": parse_number(row["Duracion"]),
                "max_speed": parse_number(row["Velocidad maxima"]),
                "driving_indicator": parse_number(row["Indicador de conduccion"]),
                "l_100km": consumption_raw / distance_m * 100,
            }
            (evaluation if date.year == 2026 else history).append(record)
    return history, evaluation


def compact_history(records: list[dict]) -> list[dict]:
    return [{"vehicle": record["vehicle"], "range": record["range"], "l_100km": record["l_100km"]} for record in records]


def aggregate(label: str, records: list[dict], total: int) -> dict:
    row = {"grupo": label, "registros": len(records), "porcentaje_sobre_evaluables": number(100 * len(records) / total) if total else 0.0, "vehiculos_implicados": len({record["vehicle"] for record in records}), "vehiculos_para_al_menos_50pct": minimal_vehicles_for_half(records)}
    for source, target in (("distance_m", "distancia_m"), ("consumption_liters", "consumo_litros"), ("l_100km", "l_100km")):
        stats = q25_50_75([record[source] for record in records])
        row.update({f"{target}_{name}": value for name, value in stats.items()})
    for source, target in (("duration_s", "duracion_s_mediana"), ("max_speed", "velocidad_maxima_mediana"), ("driving_indicator", "indicador_conduccion_mediana")):
        row[target] = q25_50_75([record[source] for record in records])["median"]
    return row


def run(input_path: Path, output_dir: Path) -> tuple[list[dict], list[dict]]:
    history, evaluation = load_records(input_path)
    vehicles, contexts = build_scopes(compact_history(history))
    evaluated = []
    for record in evaluation:
        scope = select_b30_scope(record, vehicles, contexts)
        if scope is None:
            continue
        score = robust_z(record["l_100km"], scope[0], scope[2])
        if score is not None:
            evaluated.append({**record, "robust_z": score})
    groups = [("completo_evaluable", evaluated)] + [(f"robust_z_gt_{threshold}", [record for record in evaluated if record["robust_z"] > threshold]) for threshold in THRESHOLDS]
    summary_rows = [aggregate(label, records, len(evaluated)) for label, records in groups]
    range_rows = []
    for label, records in groups:
        for range_name in RANGES:
            count = sum(record["range"] == range_name for record in records)
            range_rows.append({"grupo": label, "rango_distancia_km": range_name, "registros": count, "porcentaje_del_grupo": number(100 * count / len(records)) if records else 0.0})
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "b30_mad_extremes_2026_summary.csv", list(summary_rows[0]), summary_rows)
    write_csv(output_dir / "b30_mad_extremes_2026_by_range.csv", list(range_rows[0]), range_rows)
    return summary_rows, range_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/datos_operativa.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    rows, _ = run(args.input, args.output_dir)
    for row in rows:
        print(f"{row['grupo']}: {row['registros']} registros")


if __name__ == "__main__":
    main()
