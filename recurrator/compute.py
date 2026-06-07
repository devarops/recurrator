from collections.abc import Sequence
from datetime import date, timedelta
from statistics import median

from ._config import DEFAULT_RECURRENCE_DAYS, MIN_DAYS_GAP
from .models import Task, Context


def compute_intervals(dates: list[date | None]) -> list[int]:
    """Compute intervals in days between consecutive non-None dates."""
    valid_dates = [d for d in dates if d is not None]
    return [(b - a).days for a, b in zip(valid_dates, valid_dates[1:])]


def compute_latest_date(last_completion_date: date, skip_date: date | None) -> date:
    """Return the latest (max) of the two dates.

    last_completion_date is required (never None from CSV parsing).
    skip_date may be None if the task was never skipped.
    """
    if skip_date is None:
        return last_completion_date
    return max(last_completion_date, skip_date)


def compute_recurrence_days(intervals: Sequence[int | None]) -> int:
    """Compute recurrence days as the median of non-None intervals."""
    valid_intervals = [i for i in intervals if i is not None]
    if not valid_intervals:
        return DEFAULT_RECURRENCE_DAYS
    return round(median(valid_intervals))


def compute_due_date(latest_date: date, recurrence_days: int) -> date:
    """Return the next due date by adding recurrence_days to latest_date."""
    return latest_date + timedelta(days=recurrence_days)


def filter_four_dates(dates: list[date | None], new_date: date) -> list[date | None]:
    all_dates = sorted([d for d in dates if d is not None] + [new_date])[-4:]
    return [None] * (4 - len(all_dates)) + all_dates


def filter_all_tasks_by_context(tasks: list[Task], context: Context) -> list[Task]:
    """Filter a list of tasks by the given context."""
    return [task for task in tasks if task.context == context]


def filter_due_tasks_by_context(
    tasks: list[Task], context: Context, reference_date: date
) -> list[Task]:
    """Filter tasks by context and due/overdue status.

    Returns only tasks whose context matches and whose due date
    is on or before the reference date.
    """
    return [task for task in tasks if task.context == context and task.due_date <= reference_date]


def filter_due_tasks(tasks: list[Task], reference_date: date) -> list[Task]:
    """Filter tasks by due/overdue status.

    Returns only tasks whose due date is on or before the reference date,
    regardless of context.
    """
    return [task for task in tasks if task.due_date <= reference_date]


def filter_due_contexts(tasks: list[Task], reference_date: date) -> list[Context]:
    """Return a list of contexts that have at least one due task.

    Contexts appear sorted alphabetically by their value.
    """
    due_tasks = filter_due_tasks(tasks, reference_date)
    unique_due_contexts = {task.context for task in due_tasks}
    return sorted(unique_due_contexts, key=lambda context: context.value)


def compute_coins(recurrence_days: int, is_starred: bool) -> int:
    """Compute coins as twice the recurrence days for starred tasks."""
    return recurrence_days * 2 if is_starred else recurrence_days


def is_done_allowed(last_completion_date: date | None, reference_date: date) -> bool:
    """Return whether a task can be marked as done, rejecting same-day and consecutive-day completions."""
    if last_completion_date is None:
        return True
    return (reference_date - last_completion_date).days >= MIN_DAYS_GAP


def filter_n_tasks_by_context(
    tasks: list[Task], context: Context, reference_date: date, n_tasks: int
) -> tuple[list[Task], list[Task]]:
    """Prioritize tasks within a context by alternating-sort selection."""
    due_tasks = filter_due_tasks_by_context(tasks, context, reference_date)
    if len(due_tasks) <= n_tasks:
        return due_tasks, []
    starred_due = sorted(due_tasks, key=lambda t: not t.starred)
    selected = starred_due[:n_tasks]
    deferred = [t for t in starred_due[n_tasks:] if not t.starred]
    return selected, deferred
