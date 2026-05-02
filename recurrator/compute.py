from datetime import date
from statistics import median


def compute_intervals(dates: list[date]) -> list[int]:
    """Compute intervals in days between consecutive dates."""
    return [(b - a).days for a, b in zip(dates, dates[1:])]


def compute_latest_date(date_4: date, skipped_date: date | None) -> date:
    """Return the latest (max) of the two dates"""
    if skipped_date is None:
        return date_4
    return max(date_4, skipped_date)


def compute_recurrence_days(intervals: list[int | None]) -> int:
    """Compute recurrence days as the median of non-None intervals."""
    valid_intervals = [i for i in intervals if i is not None]
    if not valid_intervals:
        return 14
    return round(median(valid_intervals))
