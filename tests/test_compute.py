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
    assert rc.compute_intervals(dates) == [1, 1, 1]

    # Some dates missing: only one interval between valid dates
    dates = make_date_list(None, None, date(2024, 1, 2), date(2024, 1, 4))
    assert rc.compute_intervals(dates) == [2]


def test_compute_latest_date():
    """Verify compute_latest_date returns the latest date."""

    # Both dates present: returns the later date
    assert rc.compute_latest_date(date(2024, 1, 3), date(2024, 1, 2)) == date(2024, 1, 3)

    # skipped_date is None: returns date_4
    assert rc.compute_latest_date(date(2024, 1, 2), None) == date(2024, 1, 2)


def test_compute_recurrence_days():
    """Verify compute_recurrence_days returns median of intervals."""

    # All valid integers: median of [1, 2, 3] is 2
    assert rc.compute_recurrence_days([1, 2, 3]) == 2

    # Some None values: filters them, median of [14] is 14
    assert rc.compute_recurrence_days([None, None, 14]) == 14

    # All None values: returns default 14 days
    assert rc.compute_recurrence_days([None, None, None]) == 14


def test_compute_due_date():
    """Verify compute_due_date returns correct due date based on latest date and recurrence days."""

    # Latest date is 2024-01-01, recurrence is 14 days: due date should be 2024-01-15
    latest_date = date(2024, 1, 1)
    recurrence_days = 14
    expected_due_date = date(2024, 1, 15)
    assert rc.compute_due_date(latest_date, recurrence_days) == expected_due_date
