from datetime import date, timedelta
from statistics import median
from typing import Union

from .models import Task  # noqa: F401

# Default recurrence of two weeks when no interval data exists
DEFAULT_RECURRENCE_DAYS = 14


def compute_intervals(dates: list[date | None]) -> list[int]:
    """Compute intervals in days between consecutive non-None dates."""
    valid_dates = [d for d in dates if d is not None]
    return [(b - a).days for a, b in zip(valid_dates, valid_dates[1:])]


def compute_latest_date(date_4: date, skipped_date: date | None) -> date:
    """Return the latest (max) of the two dates.

    date_4 is required (never None from CSV parsing).
    skipped_date may be None if the task was never skipped.
    """
    if skipped_date is None:
        return date_4
    return max(date_4, skipped_date)


def compute_recurrence_days(intervals: Union[list[int], list[int | None]]) -> int:
    """Compute recurrence days as the median of non-None intervals."""
    valid_intervals = [i for i in intervals if i is not None]
    if not valid_intervals:
        return DEFAULT_RECURRENCE_DAYS
    return round(median(valid_intervals))


def compute_due_date(latest_date: date, recurrence_days: int) -> date:
    """Return the next due date by adding recurrence_days to latest_date."""
    return latest_date + timedelta(days=recurrence_days)


def filter_four_dates(dates: list[date | None], new_date: date) -> list[date | None]:
    valid_dates = [d for d in dates if d is not None]
    all_dates = valid_dates + [new_date]
    all_dates.sort()
    result = [None] * (4 - len(all_dates)) + all_dates
    return result[:4]


def get_task_by_id(task_id: int, csv_path: str):
    from .io import import_tasks_from_csv

    tasks = import_tasks_from_csv(csv_path)
    for task in tasks:
        if task.id == task_id:
            return task
    raise ValueError(f"Task {task_id} not found in {csv_path}")
