import recurrator.compute as rc
from datetime import date


def test_compute_intervals():
    """Verify compute_intervals returns correct day intervals."""
    date_1 = date(2024, 1, 1)
    date_2 = date(2024, 1, 2)
    date_3 = date(2024, 1, 3)
    date_4 = date(2024, 1, 4)
    expected_intervals = [1, 1, 1]
    obtained_intervals = rc.compute_intervals([date_1, date_2, date_3, date_4])
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
    intervals = [1, 2, 3]
    expected_recurrence_days = 2
    obtained_recurrence_days = rc.compute_recurrence_days(intervals)
    assert obtained_recurrence_days == expected_recurrence_days
    intervals_with_none = [None, None, 14]
    expected_recurrence_days = 14
    obtained_recurrence_days = rc.compute_recurrence_days(intervals_with_none)
    assert obtained_recurrence_days == expected_recurrence_days
    intervals_all_none = [None, None, None]
    expected_recurrence_days = 14
    obtained_recurrence_days = rc.compute_recurrence_days(intervals_all_none)
    assert obtained_recurrence_days == expected_recurrence_days
