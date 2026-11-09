import recurrator.compute as rc
import recurrator.io as io
from recurrator import Context, Task
from recurrator.models import Dates
from datetime import date


def _date_list(d1, d2, d3, d4):
    """Create a list of four dates, allowing None values."""
    return [d1, d2, d3, d4]


def test_compute_intervals():
    """Verify compute_intervals returns correct day intervals."""

    dates = _date_list(
        date(2024, 1, 1),
        date(2024, 1, 2),
        date(2024, 1, 3),
        date(2024, 1, 4),
    )
    expected_intervals = [1, 1, 1]
    obtained_intervals = rc.compute_intervals(dates)
    assert obtained_intervals == expected_intervals

    dates = _date_list(None, None, date(2024, 1, 2), date(2024, 1, 4))
    expected_intervals = [2]
    obtained_intervals = rc.compute_intervals(dates)
    assert obtained_intervals == expected_intervals


def test_compute_latest_date():
    """Verify compute_latest_date returns the latest date."""

    date_4 = date(2024, 1, 3)
    skip_date = date(2024, 1, 2)
    expected_latest_date = date_4
    obtained_latest_date = rc.compute_latest_date(date_4, skip_date)
    assert obtained_latest_date == expected_latest_date

    date_4 = date(2024, 1, 2)
    skip_date = None
    expected_latest_date = date_4
    obtained_latest_date = rc.compute_latest_date(date_4, skip_date)
    assert obtained_latest_date == expected_latest_date


def test_compute_recurrence_days():
    """Verify compute_recurrence_days returns median of intervals."""

    intervals = [1, 2, 3]
    expected_recurrence_days = 2
    obtained_recurrence_days = rc.compute_recurrence_days(intervals)
    assert obtained_recurrence_days == expected_recurrence_days

    intervals_with_none = [None, None, 7]
    expected_recurrence_days = 7
    obtained_recurrence_days = rc.compute_recurrence_days(intervals_with_none)
    assert obtained_recurrence_days == expected_recurrence_days

    intervals_all_none = [None, None, None]
    expected_recurrence_days = 14
    obtained_recurrence_days = rc.compute_recurrence_days(intervals_all_none)
    assert obtained_recurrence_days == expected_recurrence_days


def test_compute_due_date():
    """Verify compute_due_date returns correct due date based on latest date and recurrence days."""

    latest_date = date(2024, 1, 1)
    recurrence_days = 14
    expected_due_date = date(2024, 1, 15)
    obtained_due_date = rc.compute_due_date(latest_date, recurrence_days)
    assert obtained_due_date == expected_due_date


def test_compute_rolling_dates():
    """Verify compute_rolling_dates returns the four most recent dates."""
    old_dates = _date_list(
        None,
        None,
        date(2024, 1, 2),
        date(2024, 1, 4),
    )
    new_date = date(2024, 1, 6)
    expected_dates = _date_list(
        None,
        date(2024, 1, 2),
        date(2024, 1, 4),
        new_date,
    )
    obtained_dates = rc.compute_rolling_dates(old_dates, new_date)
    assert obtained_dates == expected_dates

    old_dates = _date_list(
        date(2024, 1, 4),
        None,
        date(2024, 1, 2),
        None,
    )
    new_date = date(2024, 1, 1)
    expected_dates = _date_list(
        None,
        new_date,
        date(2024, 1, 2),
        date(2024, 1, 4),
    )
    obtained_dates = rc.compute_rolling_dates(old_dates, new_date)
    assert obtained_dates == expected_dates


def test_get_task_by_id():

    obtained_task = io.get_task_by_id(3, "tests/data/test_three_tasks.csv")
    assert isinstance(obtained_task, Task)


def test_filter_all_tasks_by_context():
    all_tasks = io.import_tasks_from_csv("tests/data/test_three_tasks.csv")
    context = Context.CHORES
    filtered_tasks = rc.filter_all_tasks_by_context(all_tasks, context)
    obtained_length = len(filtered_tasks)
    expected_length = 2
    assert obtained_length == expected_length


def test_filter_due_tasks_by_context():
    all_tasks = io.import_tasks_from_csv("tests/data/test_contexts.csv")
    context = Context.CASA
    filtered_tasks = rc.filter_due_tasks_by_context(
        all_tasks, context, reference_date=date(2026, 5, 2)
    )
    obtained_length = len(filtered_tasks)
    expected_length = 2
    assert obtained_length == expected_length

    obtained_ids = [task.id for task in filtered_tasks]
    expected_ids = [1, 6]
    assert obtained_ids == expected_ids

    context = Context.CHORES
    filtered_tasks = rc.filter_due_tasks_by_context(
        all_tasks, context, reference_date=date(2026, 4, 24)
    )
    obtained_length = len(filtered_tasks)
    expected_length = 3
    assert obtained_length == expected_length

    obtained_ids = [task.id for task in filtered_tasks]
    expected_ids = [2, 4, 7]
    assert obtained_ids == expected_ids


def test_filter_due_tasks():
    all_tasks = io.import_tasks_from_csv("tests/data/test_contexts.csv")
    filtered_tasks = rc.filter_due_tasks(all_tasks, reference_date=date(2026, 4, 25))
    obtained_length = len(filtered_tasks)
    expected_length = 5
    assert obtained_length == expected_length

    obtained_ids = [task.id for task in filtered_tasks]
    expected_ids = [1, 2, 4, 7, 8]
    assert obtained_ids == expected_ids


def test_filter_due_contexts():
    all_tasks = io.import_tasks_from_csv("tests/data/test_contexts.csv")
    filtered_contexts = rc.filter_due_contexts(all_tasks, reference_date=date(2026, 5, 1))
    expected_length = 3
    obtained_length = len(filtered_contexts)
    assert obtained_length == expected_length

    expected_contexts = [Context.CASA, Context.CHORES, Context.LAPTOP]
    obtained_contexts = filtered_contexts
    assert obtained_contexts == expected_contexts


def test_compute_coins():
    """Verify compute_coins returns recurrence days for an unstarred task."""
    recurrence_days = 14
    is_starred = False
    expected_coins = 14
    obtained_coins = rc.compute_coins(recurrence_days, is_starred)
    assert obtained_coins == expected_coins

    recurrence_days = 21
    is_starred = True
    expected_coins = 42
    obtained_coins = rc.compute_coins(recurrence_days, is_starred)
    assert obtained_coins == expected_coins


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
    context = Context.CASA
    reference_date = date(2024, 1, 1)
    n_tasks = 2
    selected, deferred = rc.filter_n_tasks_by_context(tasks, context, reference_date, n_tasks)
    assert selected == []
    assert deferred == []


def test_filter_n_tasks_by_context_early_return():
    """Verify filter_n_tasks_by_context returns all due tasks when n_tasks exceeds due count."""
    tasks = io.import_tasks_from_csv("tests/data/test_three_tasks.csv")
    context = Context.CHORES
    reference_date = date(2026, 6, 6)
    n_tasks = 3
    expected_selected_tasks = rc.filter_due_tasks_by_context(tasks, context, reference_date)
    obtained_selected_tasks, deferred_tasks = rc.filter_n_tasks_by_context(
        tasks, context, reference_date, n_tasks
    )
    assert obtained_selected_tasks == expected_selected_tasks


def test_filter_n_tasks_by_context_respects_n_tasks():
    """Verify filter_n_tasks_by_context selects at most n_tasks when due tasks exceed n_tasks."""
    tasks = io.import_tasks_from_csv("tests/data/test_contexts.csv")
    context = Context.CASA
    reference_date = date(2026, 5, 2)
    n_tasks = 1
    selected, deferred = rc.filter_n_tasks_by_context(tasks, context, reference_date, n_tasks)
    obtained_length = len(selected)
    assert obtained_length == n_tasks


def test_filter_n_tasks_by_context_selects_starred_first():
    """Verify starred tasks are selected before non-starred when due tasks exceed n_tasks."""
    tasks = io.import_tasks_from_csv("tests/data/test_contexts.csv")
    context = Context.CHORES
    reference_date = date(2026, 4, 24)
    n_tasks = 2
    selected, deferred = rc.filter_n_tasks_by_context(tasks, context, reference_date, n_tasks)
    obtained_ids = [t.id for t in selected]
    expected_starred_task_id = 7
    assert expected_starred_task_id in obtained_ids


def test_filter_n_tasks_by_context_deferred_excludes_starred():
    """Verify deferred only contains non-starred tasks when all due tasks are starred."""
    tasks = io.import_tasks_from_csv("tests/data/test_contexts.csv")
    context = Context.CASA
    reference_date = date(2026, 5, 2)
    n_tasks = 1
    selected, deferred = rc.filter_n_tasks_by_context(tasks, context, reference_date, n_tasks)
    assert all(not t.starred for t in deferred)


def test_filter_n_tasks_by_context_interleaves_starred_and_non_starred():
    """Verify starred and non-starred tasks are interleaved, not all-starred-first."""
    tasks = io.import_tasks_from_csv("tests/data/test_contexts.csv")
    context = Context.CHORES
    reference_date = date(2026, 5, 10)
    n_tasks = 2
    selected, deferred = rc.filter_n_tasks_by_context(tasks, context, reference_date, n_tasks)
    assert any(not t.starred for t in selected)


def test_filter_n_tasks_by_context_sorts_non_starred_by_skip_count():
    """Verify non-starred tasks are sorted by skip_count DESC before selection."""
    reference_date = date(2026, 6, 6)
    tasks = [
        Task(
            1,
            "Low skip",
            Context.CHORES,
            0,
            False,
            Dates(date(2026, 6, 1), date(2026, 6, 1), 7, date(2026, 6, 1)),
            7,
        ),
        Task(
            2,
            "High skip",
            Context.CHORES,
            3,
            False,
            Dates(date(2026, 6, 1), date(2026, 6, 1), 7, date(2026, 6, 1)),
            7,
        ),
    ]
    expected_selected_id = 2
    selected, deferred = rc.filter_n_tasks_by_context(tasks, Context.CHORES, reference_date, 1)
    obtained_selected_id = selected[0].id
    assert obtained_selected_id == expected_selected_id


def test_filter_n_tasks_by_context_sorts_non_starred_by_recurrence_days():
    """Verify non-starred tasks with equal skip_count are sorted by recurrence_days DESC."""
    reference_date = date(2026, 6, 6)
    tasks = [
        Task(
            1,
            "Low rec",
            Context.CHORES,
            0,
            False,
            Dates(date(2026, 6, 1), date(2026, 6, 1), 7, date(2026, 6, 1)),
            7,
        ),
        Task(
            2,
            "High rec",
            Context.CHORES,
            0,
            False,
            Dates(date(2026, 6, 1), date(2026, 6, 1), 21, date(2026, 6, 1)),
            21,
        ),
    ]
    expected_selected_id = 2
    selected, deferred = rc.filter_n_tasks_by_context(tasks, Context.CHORES, reference_date, 1)
    obtained_selected_id = selected[0].id
    assert obtained_selected_id == expected_selected_id


def test_filter_n_tasks_by_context_sorts_starred_by_recurrence_days():
    """Verify starred tasks with equal skip_count and due_date are sorted by recurrence_days DESC."""
    reference_date = date(2026, 6, 6)
    tasks = [
        Task(
            1,
            "Low rec",
            Context.CHORES,
            0,
            True,
            Dates(date(2026, 6, 1), date(2026, 6, 1), 7, date(2026, 6, 1)),
            14,
        ),
        Task(
            2,
            "High rec",
            Context.CHORES,
            0,
            True,
            Dates(date(2026, 6, 1), date(2026, 6, 1), 21, date(2026, 6, 1)),
            42,
        ),
    ]
    expected_selected_id = 2
    selected, deferred = rc.filter_n_tasks_by_context(tasks, Context.CHORES, reference_date, 1)
    obtained_selected_id = selected[0].id
    assert obtained_selected_id == expected_selected_id


def test_filter_n_tasks_by_context_sorts_starred_by_skip_count():
    """Verify starred tasks are sorted by skip_count DESC before selection."""
    reference_date = date(2026, 6, 6)
    tasks = [
        Task(
            1,
            "Low skip",
            Context.CHORES,
            0,
            True,
            Dates(date(2026, 6, 1), date(2026, 6, 1), 7, date(2026, 6, 1)),
            14,
        ),
        Task(
            2,
            "High skip",
            Context.CHORES,
            3,
            True,
            Dates(date(2026, 6, 1), date(2026, 6, 1), 7, date(2026, 6, 1)),
            14,
        ),
    ]
    expected_selected_id = 2
    selected, deferred = rc.filter_n_tasks_by_context(tasks, Context.CHORES, reference_date, 1)
    obtained_selected_id = selected[0].id
    assert obtained_selected_id == expected_selected_id


def test_filter_n_tasks_by_context_sorts_starred_by_due_date():
    """Verify starred tasks with equal skip_count are sorted by due_date ASC."""
    reference_date = date(2026, 6, 6)
    tasks = [
        Task(
            1,
            "Later due",
            Context.CHORES,
            0,
            True,
            Dates(date(2026, 6, 1), date(2026, 6, 1), 7, date(2026, 6, 6)),
            14,
        ),
        Task(
            2,
            "Earlier due",
            Context.CHORES,
            0,
            True,
            Dates(date(2026, 6, 1), date(2026, 6, 1), 7, date(2026, 6, 1)),
            14,
        ),
    ]
    expected_selected_id = 2
    selected, deferred = rc.filter_n_tasks_by_context(tasks, Context.CHORES, reference_date, 1)
    obtained_selected_id = selected[0].id
    assert obtained_selected_id == expected_selected_id


def test_compute_available_wip_slots():
    """Verify compute_available_wip_slots returns remaining capacity, clamped to zero."""
    expected_value = 2
    obtained_value = rc.compute_available_wip_slots(6, 4)
    assert obtained_value == expected_value


def test_count_completed_today():
    """Verify count_completed_today counts tasks whose latest_done_date matches reference_date."""
    tasks = io.import_tasks_from_csv("tests/data/test_contexts.csv")
    obtained = rc.count_completed_today(tasks, date(2026, 2, 28))
    assert obtained == 2


def test_filter_one_extra_task_empty_list():
    """Verify filter_one_extra_task returns an empty list for an empty task list."""
    tasks: list[Task] = []
    context = Context.CASA
    reference_date = date(2026, 1, 1)
    obtained = rc.filter_one_extra_task(tasks, context, reference_date)
    assert obtained == []


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


def test_compute_universe_medians_single_task():
    """Verify a single task supplies its own rating and live deviation."""
    tasks = io.import_tasks_from_csv("tests/data/test_universe_medians.csv")

    medians = rc.compute_universe_medians(tasks, date(2026, 11, 8))

    assert medians == (1600, 350)


def test_compute_universe_medians_even_count():
    """Verify an even number of tasks returns the mean of the middle ratings."""
    tasks = io.import_tasks_from_csv("tests/data/test_universe_medians_even.csv")

    medians = rc.compute_universe_medians(tasks, date(2026, 11, 8))

    assert medians == (1550, 350)


def test_build_synthetic_opponent_uses_universe_medians():
    """Verify the synthetic opponent carries the universe medians."""
    tasks = io.import_tasks_from_csv("tests/data/test_universe_medians_even.csv")

    opponent = rc.build_synthetic_opponent(tasks, date(2026, 11, 8))

    assert (opponent.rating, opponent.rating_deviation) == (1550, 350)


def test_build_synthetic_opponent_anchors_at_reference_date():
    """Verify the synthetic opponent is anchored to the reference date."""
    tasks = io.import_tasks_from_csv("tests/data/test_universe_medians_even.csv")

    opponent = rc.build_synthetic_opponent(tasks, date(2026, 11, 8))

    assert opponent.rating_date == date(2026, 11, 8)


def test_build_synthetic_opponent_has_no_task_id():
    """Verify the synthetic opponent has no stored task id."""
    tasks = io.import_tasks_from_csv("tests/data/test_universe_medians_even.csv")

    opponent = rc.build_synthetic_opponent(tasks, date(2026, 11, 8))

    assert opponent.id is None


def test_compute_elapsed_rating_periods_for_a_year():
    """Verify a year becomes fractional rating periods."""
    periods = rc.compute_elapsed_rating_periods(date(2025, 11, 8), date(2026, 11, 8))

    assert periods == 365 * 0.21436
