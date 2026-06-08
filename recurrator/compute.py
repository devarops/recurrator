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


def compute_rolling_dates(dates: list[date | None], new_date: date) -> list[date | None]:
    """Merge new_date into a rolling window of the four most recent dates."""
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


def compute_available_wip_slots(wip_limit: int, completed_today: int) -> int:
    """Compute remaining WIP capacity, clamped to zero."""
    return max(wip_limit - completed_today, 0)


def count_completed_today(tasks: list[Task], reference_date: date) -> int:
    """Count tasks whose latest_done_date matches the reference date."""
    completed_today = [task for task in tasks if task.latest_done_date == reference_date]
    return len(completed_today)


def _sorted_tasks(tasks: list[Task], odd_cycle: bool) -> list[Task]:
    """Sort tasks by the alternating selection-order key for the given cycle."""
    if odd_cycle:
        return sorted(tasks, key=lambda t: (-t.skip_count, t.due_date, -t.recurrence_days))
    return sorted(tasks, key=lambda t: (-t.skip_count, -t.recurrence_days, t.due_date))


def filter_n_tasks_by_context(
    tasks: list[Task], context: Context, reference_date: date, available_slots: int
) -> tuple[list[Task], list[Task]]:
    """Prioritize tasks within a context by alternating-sort selection."""
    due_tasks = filter_due_tasks_by_context(tasks, context, reference_date)
    if len(due_tasks) <= available_slots:
        return due_tasks, []
    starred_pool = [t for t in due_tasks if t.starred]
    non_starred_pool = [t for t in due_tasks if not t.starred]
    selected_tasks: list[Task] = []
    odd_cycle = True
    while len(selected_tasks) < available_slots:
        starred_sorted = _sorted_tasks(starred_pool, odd_cycle)
        if starred_sorted:
            selected_tasks.append(starred_sorted[0])
            starred_pool.remove(starred_sorted[0])
        if len(selected_tasks) >= available_slots:
            break
        non_starred_sorted = _sorted_tasks(non_starred_pool, odd_cycle)
        if non_starred_sorted:
            selected_tasks.append(non_starred_sorted[0])
            non_starred_pool.remove(non_starred_sorted[0])
        odd_cycle = not odd_cycle
    deferred_tasks = non_starred_pool
    return selected_tasks, deferred_tasks
