"""Temporal split validation for offline experiments only."""


def validate_split(history_years: tuple[int, ...], evaluation_year: int) -> None:
    if not history_years or len(set(history_years)) != len(history_years):
        raise ValueError("History must contain distinct years and cannot be empty")
    if any(year >= evaluation_year for year in history_years):
        raise ValueError("Every historical year must precede evaluation")
