import recurrator.compute as rc
import recurrator.io as rio
from recurrator import Context, Task
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
    skipped_date = date(2024, 1, 2)
    expected_latest_date = date_4
    obtained_latest_date = rc.compute_latest_date(date_4, skipped_date)
    assert obtained_latest_date == expected_latest_date

    date_4 = date(2024, 1, 2)
    skipped_date = None
    expected_latest_date = date_4
    obtained_latest_date = rc.compute_latest_date(date_4, skipped_date)
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


def test_filter_four_dates():
    """Verify filter_four_dates returns the four most recent dates."""
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
    obtained_dates = rc.filter_four_dates(old_dates, new_date)
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
    obtained_dates = rc.filter_four_dates(old_dates, new_date)
    assert obtained_dates == expected_dates


def test_get_task_by_id():

    obtained_task = rio.get_task_by_id(3, "tests/data/test_three_tasks.csv")
    assert isinstance(obtained_task, Task)

def test_filter_tasks_by_context():
    all_tasks = rio.import_tasks_from_csv("tests/data/test_three_tasks.csv")
    context = Context.LIMPIAR
    filtered_tasks = rc.filter_tasks_by_context(all_tasks, context)
    obtained_length = len(filtered_tasks)
    expected_length = 2
    assert obtained_length == expected_length
