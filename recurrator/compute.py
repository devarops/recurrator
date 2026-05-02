from datetime import date


def compute_intervals(dates: list[date]) -> list[int]:
    """Compute intervals in days between consecutive dates."""
    return [(b - a).days for a, b in zip(dates, dates[1:])]
