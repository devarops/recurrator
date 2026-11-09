from collections.abc import Sequence
from datetime import date, timedelta
from statistics import median

import glicko2  # type: ignore[import-untyped]

from ._config import DEFAULT_RECURRENCE_DAYS, MIN_DAYS_GAP
from .models import (
    Context,
    GLICKO_RD_MAX,
    GLICKO_RD_MIN,
    RATING_PERIODS_PER_DAY,
    SyntheticOpponent,
    Task,
)


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


def filter_due_tasks(tasks: list[Task], reference_date: date) -> list[Task]:
    """Filter tasks by due/overdue status.

    Returns only tasks whose due date is on or before the reference date,
    regardless of context.
    """
    return [task for task in tasks if task.due_date <= reference_date]


def filter_due_tasks_by_context(
    tasks: list[Task], context: Context, reference_date: date
) -> list[Task]:
    """Filter tasks by context and due/overdue status.

    Returns only tasks whose context matches and whose due date
    is on or before the reference date.
    """
    context_tasks = filter_all_tasks_by_context(tasks, context)
    return filter_due_tasks(context_tasks, reference_date)


def filter_opponents(tasks: list[Task], completed_task: Task, reference_date: date) -> list[Task]:
    """Return other due or overdue tasks in the completed task's context."""
    due_tasks = filter_due_tasks_by_context(tasks, completed_task.context, reference_date)
    return [task for task in due_tasks if task.id != completed_task.id]


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

    def sort_key(task: Task) -> tuple:
        if odd_cycle:
            return (-task.skip_count, task.due_date, -task.recurrence_days)
        return (-task.skip_count, -task.recurrence_days, task.due_date)

    return sorted(tasks, key=sort_key)


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


def filter_one_extra_task(tasks: list[Task], context: Context, reference_date: date) -> list[Task]:
    """Return one upcoming task to pad the list when fewer than 6 tasks are due."""
    return []


def _elapsed_days(rating_date: date, reference_date: date) -> int:
    """Return the whole days since the anchor, never negative."""
    return max((reference_date - rating_date).days, 0)


def compute_elapsed_rating_periods(rating_date: date, reference_date: date) -> float:
    """Return the fractional rating periods elapsed, never negative."""
    return _elapsed_days(rating_date, reference_date) * RATING_PERIODS_PER_DAY


def compute_live_rating_deviation(
    anchored_deviation: int, rating_date: date, reference_date: date
) -> int:
    """Project an anchored rating deviation to reference_date."""
    live_deviation = anchored_deviation + _elapsed_days(rating_date, reference_date)
    return min(max(live_deviation, GLICKO_RD_MIN), GLICKO_RD_MAX)


def compute_universe_medians(tasks: list[Task], reference_date: date) -> tuple[int, int]:
    """Return the median rating and live deviation of every task."""
    ratings = [task.rating for task in tasks]
    deviations = [
        compute_live_rating_deviation(task.rating_deviation, task.rating_date, reference_date)
        for task in tasks
    ]
    return round(median(ratings)), round(median(deviations))


def build_synthetic_opponent(tasks: list[Task], reference_date: date) -> SyntheticOpponent:
    """Build an internal opponent from the universe medians."""
    rating, rating_deviation = compute_universe_medians(tasks, reference_date)
    return SyntheticOpponent(
        rating=rating, rating_deviation=rating_deviation, rating_date=reference_date
    )


def select_opponents(
    tasks: list[Task], completed_task: Task, reference_date: date
) -> Sequence[Task | SyntheticOpponent]:
    """Return the real opponents, or the synthetic one when none are due."""
    opponents = filter_opponents(tasks, completed_task, reference_date)
    if opponents:
        return opponents
    return [build_synthetic_opponent(tasks, reference_date)]


class _GlickoPlayer(glicko2.Player):
    def _preRatingRD(self):
        """The elapsed-time projection already set the pre-event deviation."""


def compute_match_updates(
    completed_task: Task,
    opponents: Sequence[Task | SyntheticOpponent],
    reference_date: date,
) -> dict[int, tuple[int, int]]:
    """Return simultaneous rating and deviation updates for one completion."""
    participants: list[Task | SyntheticOpponent] = [completed_task, *opponents]
    players: dict[int | None, _GlickoPlayer] = {
        task.id: _GlickoPlayer(
            task.rating,
            compute_live_rating_deviation(task.rating_deviation, task.rating_date, reference_date),
        )
        for task in participants
    }
    snapshot_ratings = {task_id: player.getRating() for task_id, player in players.items()}
    snapshot_deviations = {task_id: player.getRd() for task_id, player in players.items()}

    completed_id = completed_task.id
    opponent_ids: list[int | None] = [task.id for task in opponents]
    updates: dict[int, tuple[int, int]] = {}

    def play(task_id: int, opponents_for_task: Sequence[int | None], outcomes: list[float]) -> None:
        player = players[task_id]
        player.update_player(
            [snapshot_ratings[opponent_id] for opponent_id in opponents_for_task],
            [snapshot_deviations[opponent_id] for opponent_id in opponents_for_task],
            outcomes,
        )
        updates[task_id] = (round(player.getRating()), round(player.getRd()))

    completed_outcomes = [0.0] * len(opponent_ids)
    opponent_outcomes = [1.0]
    play(completed_id, opponent_ids, completed_outcomes)
    for opponent_id in opponent_ids:
        if opponent_id is None:
            continue
        play(opponent_id, [completed_id], opponent_outcomes)
    return updates
