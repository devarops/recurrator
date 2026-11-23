from collections.abc import Sequence
from datetime import date, timedelta
from math import sqrt
from statistics import median

import glicko2  # type: ignore[import-untyped]

from ._config import DEFAULT_RECURRENCE_DAYS, MIN_DAYS_GAP
from .models import (
    GLICKO_RATING_DEVIATION_MAX,
    GLICKO_RATING_DEVIATION_MIN,
    GLICKO_RATING_PERIODS_PER_DAY,
    GLICKO_SCALE,
    GLICKO_VOLATILITY_DEFAULT,
    N_DATES,
    SyntheticOpponent,
    Task,
)


def compute_intervals(dates: list[date | None]) -> list[int]:
    """Compute intervals in days between consecutive non-None dates."""
    valid_dates = [date_value for date_value in dates if date_value is not None]
    return [(later - earlier).days for earlier, later in zip(valid_dates, valid_dates[1:])]


def compute_latest_date(latest_done_date: date, skip_date: date | None) -> date:
    """Return the latest (max) of the two dates.

    latest_done_date is required (never None from CSV parsing).
    skip_date may be None if the task was never skipped.
    """
    if skip_date is None:
        return latest_done_date
    return max(latest_done_date, skip_date)


def compute_recurrence_days(intervals: Sequence[int | None]) -> int:
    """Compute recurrence days as the median of non-None intervals."""
    valid_intervals = [interval for interval in intervals if interval is not None]
    if not valid_intervals:
        return DEFAULT_RECURRENCE_DAYS
    return round(median(valid_intervals))


def compute_due_date(latest_date: date, recurrence_days: int) -> date:
    """Return the next due date by adding recurrence_days to latest_date."""
    return latest_date + timedelta(days=recurrence_days)


def compute_rolling_dates(dates: list[date | None], new_date: date) -> list[date | None]:
    """Merge new_date into a rolling window of the most recent stored dates."""
    stored_dates = [stored_date for stored_date in dates if stored_date is not None]
    all_dates = sorted(stored_dates + [new_date])[-N_DATES:]
    return [None] * (N_DATES - len(all_dates)) + all_dates


def filter_tasks_by_any_context(tasks: list[Task], contexts: set[str]) -> list[Task]:
    """Filter tasks that name at least one of the given context ids."""
    return [task for task in tasks if contexts & set(task.contexts)]


def filter_tasks_by_context(tasks: list[Task], context: str) -> list[Task]:
    """Filter tasks by the given context id."""
    return filter_tasks_by_any_context(tasks, {context})


def filter_due_tasks(tasks: list[Task], reference_date: date) -> list[Task]:
    """Filter tasks by due/overdue status.

    Returns only tasks whose due date is on or before the reference date,
    regardless of context.
    """
    return [task for task in tasks if task.due_date <= reference_date]


def filter_due_tasks_by_any_context(
    tasks: list[Task], contexts: set[str], reference_date: date
) -> list[Task]:
    """Filter due tasks that name at least one of the given context ids."""
    due_tasks = filter_due_tasks(tasks, reference_date)
    return filter_tasks_by_any_context(due_tasks, contexts)


def filter_due_tasks_by_context(
    tasks: list[Task], context: str, reference_date: date
) -> list[Task]:
    """Filter tasks by context and due/overdue status.

    Returns only tasks whose context matches and whose due date
    is on or before the reference date.
    """
    return filter_due_tasks_by_any_context(tasks, {context}, reference_date)


def filter_opponents(tasks: list[Task], completed_task: Task, reference_date: date) -> list[Task]:
    """Return other due tasks that share at least one context with the completed task."""
    sharing_context = filter_due_tasks_by_any_context(
        tasks, set(completed_task.contexts), reference_date
    )
    return [task for task in sharing_context if task.id != completed_task.id]


def filter_due_contexts(tasks: list[Task], reference_date: date) -> list[str]:
    """Return the context ids that have at least one due task, sorted."""
    due_contexts = {
        context for task in filter_due_tasks(tasks, reference_date) for context in task.contexts
    }
    return sorted(due_contexts)


def compute_coins(recurrence_days: int, is_starred: bool) -> int:
    """Compute coins as twice the recurrence days for starred tasks."""
    return recurrence_days * 2 if is_starred else recurrence_days


def is_done_allowed(latest_done_date: date | None, reference_date: date) -> bool:
    """Return whether a task can be marked as done, rejecting same-day and consecutive-day completions."""
    if latest_done_date is None:
        return True
    return (reference_date - latest_done_date).days >= MIN_DAYS_GAP


def compute_available_wip_slots(wip_limit: int, completed_count: int) -> int:
    """Compute remaining WIP capacity, clamped to zero."""
    return max(wip_limit - completed_count, 0)


def count_completed_on(tasks: list[Task], reference_date: date) -> int:
    """Count tasks whose latest_done_date matches the reference date."""
    completed_tasks = [task for task in tasks if task.latest_done_date == reference_date]
    return len(completed_tasks)


def _take_top_task(pool: list[Task], odd_cycle: bool) -> Task | None:
    """Remove and return the highest-priority task in the pool, if any."""
    if not pool:
        return None

    def selection_key(task: Task) -> tuple:
        if odd_cycle:
            return (-task.skip_count, task.due_date, -task.recurrence_days)
        return (-task.skip_count, -task.recurrence_days, task.due_date)

    top_task = min(pool, key=selection_key)
    pool.remove(top_task)
    return top_task


def filter_n_tasks_by_context(
    tasks: list[Task], context: str, reference_date: date, available_slots: int
) -> tuple[list[Task], list[Task]]:
    """Prioritize tasks within a context by alternating-sort selection."""
    due_tasks = filter_due_tasks_by_context(tasks, context, reference_date)
    if len(due_tasks) <= available_slots:
        return due_tasks, []
    starred_pool = [task for task in due_tasks if task.starred]
    non_starred_pool = [task for task in due_tasks if not task.starred]
    selected_tasks: list[Task] = []
    odd_cycle = True
    while len(selected_tasks) < available_slots:
        starred_task = _take_top_task(starred_pool, odd_cycle)
        if starred_task is not None:
            selected_tasks.append(starred_task)
            if len(selected_tasks) >= available_slots:
                break
        non_starred_task = _take_top_task(non_starred_pool, odd_cycle)
        if non_starred_task is not None:
            selected_tasks.append(non_starred_task)
        odd_cycle = not odd_cycle
    deferred_tasks = non_starred_pool
    return selected_tasks, deferred_tasks


def filter_one_extra_task(tasks: list[Task], context: str, reference_date: date) -> list[Task]:
    """Return one upcoming task to pad a non-empty list that is under the WIP limit."""
    return []


def compute_elapsed_rating_periods(rating_date: date, reference_date: date) -> float:
    """Return the fractional rating periods elapsed, never negative."""
    elapsed_days = max((reference_date - rating_date).days, 0)
    return elapsed_days * GLICKO_RATING_PERIODS_PER_DAY


def compute_live_rating_deviation(
    anchored_deviation: int, rating_date: date, reference_date: date
) -> float:
    """Project an anchored rating deviation to reference_date."""
    elapsed_periods = compute_elapsed_rating_periods(rating_date, reference_date)
    growth_per_period = (GLICKO_SCALE * GLICKO_VOLATILITY_DEFAULT) ** 2
    live_deviation = sqrt(anchored_deviation**2 + growth_per_period * elapsed_periods)
    return min(max(live_deviation, GLICKO_RATING_DEVIATION_MIN), GLICKO_RATING_DEVIATION_MAX)


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
