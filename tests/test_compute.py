import recurrator.compute as rc
import recurrator.io as io
from recurrator import Task
from recurrator.models import Dates
from datetime import date
from conftest import CONTEXT_TASKS_CSV, THREE_TASKS_CSV, UNIVERSE_MEDIANS_EVEN_CSV


def _chores_task(
    task_id: int,
    description: str,
    skip_count: int = 0,
    starred: bool = False,
    recurrence_days: int = 7,
    due_date: date = date(2026, 6, 1),
) -> Task:
    """Build a chores task whose dates and coins follow the given schedule."""
    dates = Dates(date(2026, 6, 1), date(2026, 6, 1), recurrence_days, due_date)
    return Task(
        task_id,
        description,
        ["chores"],
        skip_count,
        starred,
        dates,
        rc.compute_coins(recurrence_days, starred),
    )


def _selected_task_id(tasks, reference_date, available_slots):
    """Return the id of the top task the prioritizer selects."""
    selected, _ = rc.filter_n_tasks_by_context(tasks, "chores", reference_date, available_slots)
    return selected[0].id


def _even_universe_opponent():
    """Build the synthetic opponent from the even-sized universe at the glicko date."""
    tasks = io.import_tasks_from_csv(UNIVERSE_MEDIANS_EVEN_CSV)
    return rc.build_synthetic_opponent(tasks, date(2026, 11, 8))


def test_compute_intervals():
    """Verify compute_intervals returns correct day intervals."""

    dates = [
        date(2024, 1, 1),
        date(2024, 1, 2),
        date(2024, 1, 3),
        date(2024, 1, 4),
    ]
    assert rc.compute_intervals(dates) == [1, 1, 1]

    dates = [None, None, date(2024, 1, 2), date(2024, 1, 4)]
    assert rc.compute_intervals(dates) == [2]


def test_compute_latest_date():
    """Verify compute_latest_date returns the latest date."""

    date_4 = date(2024, 1, 3)
    skip_date = date(2024, 1, 2)
    assert rc.compute_latest_date(date_4, skip_date) == date_4

    date_4 = date(2024, 1, 2)
    skip_date = None
    assert rc.compute_latest_date(date_4, skip_date) == date_4


def test_compute_recurrence_days():
    """Verify compute_recurrence_days returns median of intervals."""

    intervals = [1, 2, 3]
    assert rc.compute_recurrence_days(intervals) == 2

    intervals_with_none = [None, None, 7]
    assert rc.compute_recurrence_days(intervals_with_none) == 7

    intervals_all_none = [None, None, None]
    assert rc.compute_recurrence_days(intervals_all_none) == 14


def test_compute_due_date():
    """Verify compute_due_date returns correct due date based on latest date and recurrence days."""

    latest_date = date(2024, 1, 1)
    recurrence_days = 14
    assert rc.compute_due_date(latest_date, recurrence_days) == date(2024, 1, 15)


def test_compute_rolling_dates():
    """Verify compute_rolling_dates returns the four most recent dates."""
    old_dates = [None, None, date(2024, 1, 2), date(2024, 1, 4)]
    new_date = date(2024, 1, 6)
    expected_dates = [None, date(2024, 1, 2), date(2024, 1, 4), new_date]
    assert rc.compute_rolling_dates(old_dates, new_date) == expected_dates

    old_dates = [date(2024, 1, 4), None, date(2024, 1, 2), None]
    new_date = date(2024, 1, 1)
    expected_dates = [None, new_date, date(2024, 1, 2), date(2024, 1, 4)]
    assert rc.compute_rolling_dates(old_dates, new_date) == expected_dates


def test_get_task_by_id():

    assert isinstance(io.get_task_by_id(3, THREE_TASKS_CSV), Task)


def test_filter_tasks_by_context():
    all_tasks = io.import_tasks_from_csv(THREE_TASKS_CSV)
    context = "chores"
    filtered_tasks = rc.filter_tasks_by_context(all_tasks, context)
    assert len(filtered_tasks) == 2


def test_filter_due_tasks_by_context():
    all_tasks = io.import_tasks_from_csv(CONTEXT_TASKS_CSV)
    context = "casa"
    filtered_tasks = rc.filter_due_tasks_by_context(
        all_tasks, context, reference_date=date(2026, 5, 2)
    )
    assert len(filtered_tasks) == 2
    assert [task.id for task in filtered_tasks] == [1, 6]

    context = "chores"
    filtered_tasks = rc.filter_due_tasks_by_context(
        all_tasks, context, reference_date=date(2026, 4, 24)
    )
    assert len(filtered_tasks) == 3
    assert [task.id for task in filtered_tasks] == [2, 4, 7]


def test_filter_due_tasks():
    all_tasks = io.import_tasks_from_csv(CONTEXT_TASKS_CSV)
    filtered_tasks = rc.filter_due_tasks(all_tasks, reference_date=date(2026, 4, 25))
    assert len(filtered_tasks) == 5
    assert [task.id for task in filtered_tasks] == [1, 2, 4, 7, 8]


def test_filter_due_contexts():
    all_tasks = io.import_tasks_from_csv(CONTEXT_TASKS_CSV)
    filtered_contexts = rc.filter_due_contexts(all_tasks, reference_date=date(2026, 5, 1))
    assert len(filtered_contexts) == 3
    assert filtered_contexts == ["casa", "chores", "laptop"]


def test_compute_coins():
    """Verify compute_coins returns recurrence days for an unstarred task."""
    recurrence_days = 14
    is_starred = False
    assert rc.compute_coins(recurrence_days, is_starred) == 14

    recurrence_days = 21
    is_starred = True
    assert rc.compute_coins(recurrence_days, is_starred) == 42


def test_is_done_allowed():
    """Verify is_done_allowed rejects same-day and consecutive-day completions."""
    today = date(2026, 5, 24)

    assert rc.is_done_allowed(today, today) is False
    assert rc.is_done_allowed(date(2026, 5, 23), today) is False
    assert rc.is_done_allowed(date(2026, 5, 22), today) is True
    assert rc.is_done_allowed(None, today) is True


def test_filter_n_tasks_by_context_empty_list():
    """Verify filter_n_tasks_by_context returns ([], []) for an empty task list."""
    tasks = []
    context = "casa"
    reference_date = date(2024, 1, 1)
    n_tasks = 2
    selected, deferred = rc.filter_n_tasks_by_context(tasks, context, reference_date, n_tasks)
    assert selected == []
    assert deferred == []


def test_filter_n_tasks_by_context_early_return():
    """Verify filter_n_tasks_by_context returns all due tasks when n_tasks exceeds due count."""
    tasks = io.import_tasks_from_csv(THREE_TASKS_CSV)
    context = "chores"
    reference_date = date(2026, 6, 6)
    n_tasks = 3
    expected_selected_tasks = rc.filter_due_tasks_by_context(tasks, context, reference_date)
    obtained_selected_tasks, _ = rc.filter_n_tasks_by_context(
        tasks, context, reference_date, n_tasks
    )
    assert obtained_selected_tasks == expected_selected_tasks


def test_filter_n_tasks_by_context_respects_n_tasks():
    """Verify filter_n_tasks_by_context selects at most n_tasks when due tasks exceed n_tasks."""
    tasks = io.import_tasks_from_csv(CONTEXT_TASKS_CSV)
    context = "casa"
    reference_date = date(2026, 5, 2)
    n_tasks = 1
    selected, _ = rc.filter_n_tasks_by_context(tasks, context, reference_date, n_tasks)
    assert len(selected) == n_tasks


def test_filter_n_tasks_by_context_selects_starred_first():
    """Verify starred tasks are selected before non-starred when due tasks exceed n_tasks."""
    tasks = io.import_tasks_from_csv(CONTEXT_TASKS_CSV)
    context = "chores"
    reference_date = date(2026, 4, 24)
    n_tasks = 2
    selected, _ = rc.filter_n_tasks_by_context(tasks, context, reference_date, n_tasks)
    assert 7 in [task.id for task in selected]


def test_filter_n_tasks_by_context_deferred_excludes_starred():
    """Verify deferred only contains non-starred tasks when all due tasks are starred."""
    tasks = io.import_tasks_from_csv(CONTEXT_TASKS_CSV)
    context = "casa"
    reference_date = date(2026, 5, 2)
    n_tasks = 1
    _, deferred = rc.filter_n_tasks_by_context(tasks, context, reference_date, n_tasks)
    assert all(not t.starred for t in deferred)


def test_filter_n_tasks_by_context_interleaves_starred_and_non_starred():
    """Verify starred and non-starred tasks are interleaved, not all-starred-first."""
    tasks = io.import_tasks_from_csv(CONTEXT_TASKS_CSV)
    context = "chores"
    reference_date = date(2026, 5, 10)
    n_tasks = 2
    selected, _ = rc.filter_n_tasks_by_context(tasks, context, reference_date, n_tasks)
    assert any(not t.starred for t in selected)


def test_filter_n_tasks_by_context_sorts_non_starred_by_skip_count():
    """Verify non-starred tasks are sorted by skip_count DESC before selection."""
    reference_date = date(2026, 6, 6)
    tasks = [
        _chores_task(1, "Low skip"),
        _chores_task(2, "High skip", skip_count=3),
    ]
    assert _selected_task_id(tasks, reference_date, 1) == 2


def test_filter_n_tasks_by_context_sorts_non_starred_by_recurrence_days():
    """Verify non-starred tasks with equal skip_count are sorted by recurrence_days DESC."""
    reference_date = date(2026, 6, 6)
    tasks = [
        _chores_task(1, "Low rec"),
        _chores_task(2, "High rec", recurrence_days=21),
    ]
    assert _selected_task_id(tasks, reference_date, 1) == 2


def test_filter_n_tasks_by_context_sorts_starred_by_recurrence_days():
    """Verify starred tasks with equal skip_count and due_date are sorted by recurrence_days DESC."""
    reference_date = date(2026, 6, 6)
    tasks = [
        _chores_task(1, "Low rec", starred=True),
        _chores_task(2, "High rec", starred=True, recurrence_days=21),
    ]
    assert _selected_task_id(tasks, reference_date, 1) == 2


def test_filter_n_tasks_by_context_sorts_starred_by_skip_count():
    """Verify starred tasks are sorted by skip_count DESC before selection."""
    reference_date = date(2026, 6, 6)
    tasks = [
        _chores_task(1, "Low skip", starred=True),
        _chores_task(2, "High skip", starred=True, skip_count=3),
    ]
    assert _selected_task_id(tasks, reference_date, 1) == 2


def test_filter_n_tasks_by_context_second_selection_prefers_more_skips():
    """Verify the even cycle selects the task with more skips first."""
    reference_date = date(2026, 6, 6)
    tasks = [
        _chores_task(1, "Most skips", skip_count=5),
        _chores_task(2, "Some skips", skip_count=3),
        _chores_task(3, "No skips"),
    ]
    selected, _ = rc.filter_n_tasks_by_context(tasks, "chores", reference_date, 2)
    assert [task.id for task in selected] == [1, 2]


def test_filter_n_tasks_by_context_second_selection_prefers_longer_recurrence():
    """Verify the even cycle selects the longer recurrence before the shorter one."""
    reference_date = date(2026, 6, 6)
    tasks = [
        _chores_task(1, "First due", due_date=date(2026, 6, 1)),
        _chores_task(2, "Longer recurrence", recurrence_days=21, due_date=date(2026, 6, 6)),
        _chores_task(3, "Shorter recurrence", recurrence_days=7, due_date=date(2026, 6, 6)),
    ]
    selected, _ = rc.filter_n_tasks_by_context(tasks, "chores", reference_date, 2)
    assert [task.id for task in selected] == [1, 2]


def test_filter_n_tasks_by_context_prefers_due_date_over_recurrence():
    """Verify the first selection orders by due date before recurrence days."""
    reference_date = date(2026, 6, 6)
    tasks = [
        _chores_task(1, "Earlier due", due_date=date(2026, 6, 1)),
        _chores_task(2, "Longer recurrence", recurrence_days=21, due_date=date(2026, 6, 6)),
    ]
    assert _selected_task_id(tasks, reference_date, 1) == 1


def test_filter_n_tasks_by_context_sorts_starred_by_due_date():
    """Verify starred tasks with equal skip_count are sorted by due_date ASC."""
    reference_date = date(2026, 6, 6)
    tasks = [
        _chores_task(1, "Later due", starred=True, due_date=date(2026, 6, 6)),
        _chores_task(2, "Earlier due", starred=True),
    ]
    assert _selected_task_id(tasks, reference_date, 1) == 2


def test_compute_available_wip_slots():
    """Verify compute_available_wip_slots returns remaining capacity, clamped to zero."""
    assert rc.compute_available_wip_slots(6, 4) == 2


def test_compute_available_wip_slots_clamps_to_zero():
    """Verify capacity never falls below zero when completions reach or pass the limit."""
    assert rc.compute_available_wip_slots(6, 6) == 0
    assert rc.compute_available_wip_slots(6, 7) == 0


def test_count_completed_today():
    """Verify count_completed_today counts tasks whose latest_done_date matches reference_date."""
    tasks = io.import_tasks_from_csv(CONTEXT_TASKS_CSV)
    assert rc.count_completed_today(tasks, date(2026, 2, 28)) == 2


def test_filter_one_extra_task_empty_list():
    """Verify filter_one_extra_task returns an empty list for an empty task list."""
    tasks: list[Task] = []
    context = "casa"
    reference_date = date(2026, 1, 1)
    assert rc.filter_one_extra_task(tasks, context, reference_date) == []


def test_compute_elapsed_rating_periods_for_a_year():
    """Verify a year becomes fractional rating periods."""
    periods = rc.compute_elapsed_rating_periods(date(2025, 11, 8), date(2026, 11, 8))

    assert periods == 365 * 0.21436


def test_compute_live_rating_deviation_without_elapsed_time():
    """Verify the anchored rating deviation is unchanged on its anchor date."""
    anchor = date(2026, 11, 8)

    assert rc.compute_live_rating_deviation(350, anchor, anchor) == 350


def test_compute_live_rating_deviation_clamps_to_minimum():
    """Verify a projected deviation below the minimum is raised to 45."""
    anchor = date(2026, 11, 8)

    assert rc.compute_live_rating_deviation(20, anchor, anchor) == 45


def test_compute_live_rating_deviation_clamps_to_maximum():
    """Verify a projected deviation above the maximum is lowered to 500."""
    anchor = date(2026, 11, 8)

    assert rc.compute_live_rating_deviation(600, anchor, anchor) == 500


def test_compute_live_rating_deviation_grows_after_elapsed_time():
    """Verify a later reference date increases the anchored deviation."""
    anchor = date(2026, 11, 8)
    later = date(2026, 11, 9)

    assert rc.compute_live_rating_deviation(350, anchor, later) > 350


def test_compute_live_rating_deviation_grows_more_with_more_elapsed_time():
    """Verify a longer elapsed time produces a larger deviation."""
    anchor = date(2026, 11, 8)
    one_day = date(2026, 11, 9)
    two_days = date(2026, 11, 10)

    assert rc.compute_live_rating_deviation(
        350, anchor, two_days
    ) > rc.compute_live_rating_deviation(350, anchor, one_day)


def test_compute_live_rating_deviation_grows_less_than_one_point_per_day():
    """Verify a day of elapsed time adds less than one rating-deviation point."""
    anchor = date(2026, 11, 8)
    later = date(2026, 11, 9)

    assert rc.compute_live_rating_deviation(350, anchor, later) < 351


def test_compute_universe_medians_single_task():
    """Verify a single task supplies its own rating and live deviation."""
    tasks = io.import_tasks_from_csv("tests/data/test_universe_medians.csv")

    medians = rc.compute_universe_medians(tasks, date(2026, 11, 8))

    assert medians == (1600, 350)


def test_compute_universe_medians_even_count():
    """Verify an even number of tasks returns the mean of the middle ratings."""
    tasks = io.import_tasks_from_csv(UNIVERSE_MEDIANS_EVEN_CSV)

    medians = rc.compute_universe_medians(tasks, date(2026, 11, 8))

    assert medians == (1550, 350)


def test_build_synthetic_opponent_uses_universe_medians():
    """Verify the synthetic opponent carries the universe medians."""
    opponent = _even_universe_opponent()

    assert (opponent.rating, opponent.rating_deviation) == (1550, 350)


def test_build_synthetic_opponent_anchors_at_reference_date():
    """Verify the synthetic opponent is anchored to the reference date."""
    opponent = _even_universe_opponent()

    assert opponent.rating_date == date(2026, 11, 8)


def test_build_synthetic_opponent_has_no_task_id():
    """Verify the synthetic opponent has no stored task id."""
    opponent = _even_universe_opponent()

    assert opponent.id is None
