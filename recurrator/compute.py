from datetime import date


def compute_intervals(dates: list[date]) -> list[int]:
    """Compute intervals in days between consecutive dates."""
    return [(b - a).days for a, b in zip(dates, dates[1:])]


def compute_latest_date(date_4: date | None, skipped_date: date | None) -> date | None:
    """Return the latest (max) of the two dates, handling None."""
    if date_4 is None and skipped_date is None:
        return None
    if date_4 is None:
        return skipped_date
    if skipped_date is None:
        return date_4
    return max(date_4, skipped_date)
