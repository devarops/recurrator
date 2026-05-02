from datetime import date


def compute_intervals(dates: list[date]) -> list[int]:
    """Compute intervals in days between consecutive dates."""
    return [(b - a).days for a, b in zip(dates, dates[1:])]


def compute_latest_date(date_4: date, skipped_date: date) -> date:
    """Return the latest (max) of the two dates."""
    return max(date_4, skipped_date)
