import recurrator.compute as rc
from datetime import date


def make_date_list(d1, d2, d3, d4):
    """Create a list of four dates, allowing None values."""
    return [d1, d2, d3, d4]


def test_compute_intervals():
    """Verify compute_intervals returns correct day intervals."""

    # All consecutive dates: 1-day intervals
    dates = make_date_list(
        date(2024, 1, 1),
        date(2024, 1, 2),
        date(2024, 1, 3),
        date(2024, 1, 4),
    )
    expected_intervals = [1, 1, 1]
    obtained_intervals = rc.compute_intervals(dates)
    assert obtained_intervals == expected_intervals

    # Some dates missing: only one interval between valid dates
    dates = make_date_list(None, None, date(2024, 1, 2), date(2024, 1, 4))
    expected_intervals = [2]
    obtained_intervals = rc.compute_intervals(dates)
    assert obtained_intervals == expected_intervals


def test_compute_latest_date():
    """Verify compute_latest_date returns the latest date."""

    # Both dates present: returns the later date
    date_4 = date(2024, 1, 3)
    skipped_date = date(2024, 1, 2)
    expected_latest_date = date_4
    obtained_latest_date = rc.compute_latest_date(date_4, skipped_date)
    assert obtained_latest_date == expected_latest_date

    # skipped_date is None: returns date_4
    date_4 = date(2024, 1, 2)
    skipped_date = None
    expected_latest_date = date_4
    obtained_latest_date = rc.compute_latest_date(date_4, skipped_date)
    assert obtained_latest_date == expected_latest_date


def test_compute_recurrence_days():
    """Verify compute_recurrence_days returns median of intervals."""

    # All valid integers: median of [1, 2, 3] is 2
    intervals = [1, 2, 3]
    expected_recurrence_days = 2
    obtained_recurrence_days = rc.compute_recurrence_days(intervals)
    assert obtained_recurrence_days == expected_recurrence_days

    # Some None values: filters them, median of [14] is 14
    intervals_with_none = [None, None, 14]
    expected_recurrence_days = 14
    obtained_recurrence_days = rc.compute_recurrence_days(intervals_with_none)
    assert obtained_recurrence_days == expected_recurrence_days

    # All None values: returns default 14 days
    intervals_all_none = [None, None, None]
    expected_recurrence_days = 14
    obtained_recurrence_days = rc.compute_recurrence_days(intervals_all_none)
    assert obtained_recurrence_days == expected_recurrence_days


def test_compute_due_date():
    """Verify compute_due_date returns correct due date based on latest date and recurrence days."""

    # Latest date is 2024-01-01, recurrence is 14 days: due date should be 2024-01-15
    latest_date = date(2024, 1, 1)
    recurrence_days = 14
    expected_due_date = date(2024, 1, 15)
    obtained_due_date = rc.compute_due_date(latest_date, recurrence_days)
    assert obtained_due_date == expected_due_date
