"""Genera un perfil exploratorio local del CSV de operativa.

El script solo lee el CSV original y escribe un informe agregado en una ruta
local (por defecto, dentro de data/, que está ignorada por Git).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PERCENTILES = (0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)
STAT_LABELS = ("min", "P01", "P05", "P10", "P25", "mediana", "P75", "P90", "P95", "P99", "max")


def parse_numeric(values: pd.Series) -> pd.Series:
    """Convierte números con coma decimal sin modificar la fuente."""
    text = values.astype("string").str.strip().str.replace("\u00a0", "", regex=False)
    has_comma = text.str.contains(",", regex=False, na=False)
    has_dot = text.str.contains(".", regex=False, na=False)
    both = has_comma & has_dot
    text = text.mask(both, text.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    text = text.mask(has_comma & ~has_dot, text.str.replace(",", ".", regex=False))
    return pd.to_numeric(text, errors="coerce")


def distribution(values: pd.Series) -> dict[str, float]:
    clean = values.dropna()
    result = {"min": clean.min()}
    result.update({label: clean.quantile(percentile) for label, percentile in zip(STAT_LABELS[1:-1], PERCENTILES)})
    result["max"] = clean.max()
    return result


def number(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")


def distribution_table(values: pd.Series) -> list[str]:
    stats = distribution(values)
    return [
        "| Estadístico | Valor |",
        "| --- | ---: |",
        *[f"| {label} | {number(stats[label])} |" for label in STAT_LABELS],
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Perfil estadístico exploratorio del CSV local.")
    parser.add_argument("--input", type=Path, default=Path("data/datos_operativa.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/perfil_estadistico.md"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.input, encoding="utf-8-sig", sep=";", dtype="string")

    for column in ("Duracion", "Distancia", "Consumo"):
        df[f"_{column}_numeric"] = parse_numeric(df[column])
    dates = pd.to_datetime(df["Fecha de inicio"], errors="coerce", format="mixed", dayfirst=True)
    df["_year"] = dates.dt.year

    valid_ratio = (df["_Consumo_numeric"] > 0) & (df["_Distancia_numeric"] > 0)
    exploratory = df.loc[valid_ratio].copy()
    exploratory["distancia_km"] = exploratory["_Distancia_numeric"] / 1000
    exploratory["consumo_litros"] = exploratory["_Consumo_numeric"] / 1000
    exploratory["consumo_l_100km"] = exploratory["consumo_litros"] / exploratory["distancia_km"] * 100

    by_vehicle = (
        df.assign(
            consumo_positivo=df["_Consumo_numeric"] > 0,
            consumo_cero=df["_Consumo_numeric"] == 0,
        )
        .groupby("Codigo Vehiculo", dropna=False)
        .agg(
            registros=("Codigo Viaje", "size"),
            consumo_positivo=("consumo_positivo", "sum"),
            consumo_cero=("consumo_cero", "sum"),
        )
        .sort_index()
    )

    lines = [
        "# Perfil estadístico exploratorio local",
        "",
        "Informe generado por `scripts/profile_dataset.py`. El CSV no se modifica.",
        "",
        "## Cobertura",
        "",
        f"- Registros totales: {len(df)}",
        f"- Registros 2024: {(df['_year'] == 2024).sum()}",
        f"- Registros 2025: {(df['_year'] == 2025).sum()}",
        f"- Registros 2026: {(df['_year'] == 2026).sum()}",
        "",
        "## Registros por vehículo",
        "",
        "| Codigo Vehiculo | Registros | Consumo > 0 | Consumo = 0 |",
        "| --- | ---: | ---: | ---: |",
    ]
    lines.extend(
        f"| {vehicle} | {row.registros} | {row.consumo_positivo} | {row.consumo_cero} |"
        for vehicle, row in by_vehicle.iterrows()
    )

    for title, column in (
        ("Distribución de Distancia", "_Distancia_numeric"),
        ("Distribución de Duracion", "_Duracion_numeric"),
        ("Distribución de Consumo positivo", "_Consumo_numeric"),
    ):
        values = df[column] if title != "Distribución de Consumo positivo" else df.loc[df[column] > 0, column]
        lines.extend(["", f"## {title}", "", *distribution_table(values)])

    lines.extend(["", "## Registros con Consumo > 0 y Distancia > 0", "", f"- Registros: {len(exploratory)}"])
    lines.extend(["", "## Distribución de consumo L/100 km", "", *distribution_table(exploratory["consumo_l_100km"])])

    lines.extend(["", "## Distribución de L/100 km por año", ""])
    for year in (2024, 2025, 2026):
        year_values = exploratory.loc[exploratory["_year"] == year, "consumo_l_100km"]
        lines.extend([f"### {year} ({len(year_values)} registros)", "", *distribution_table(year_values), ""])

    top = exploratory.nlargest(20, "consumo_l_100km")
    lines.extend(
        [
            "## 20 valores más altos de L/100 km",
            "",
            "| Codigo Vehiculo | Codigo Viaje | Fecha de inicio | Duracion | Distancia | Consumo | L/100km |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in top.iterrows():
        lines.append(
            "| {vehicle} | {trip} | {date} | {duration} | {distance} | {consumption} | {l100} |".format(
                vehicle=row["Codigo Vehiculo"],
                trip=row["Codigo Viaje"],
                date=row["Fecha de inicio"],
                duration=number(row["_Duracion_numeric"]),
                distance=number(row["_Distancia_numeric"]),
                consumption=number(row["_Consumo_numeric"]),
                l100=number(row["consumo_l_100km"]),
            )
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
