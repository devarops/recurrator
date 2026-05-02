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
    expected_latest_date = date(2024, 1, 3)
    obtained_latest_date = rc.compute_latest_date(date_4, skipped_date)
    assert obtained_latest_date == expected_latest_date
