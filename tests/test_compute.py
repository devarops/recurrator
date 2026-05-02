import recurrator.compute as rc
from datetime import date


def test_compute_intervals():
    """Verify compute_intervals returns correct day intervals."""
    date1 = date(2024, 1, 1)
    date2 = date(2024, 1, 2)
    date3 = date(2024, 1, 3)
    date4 = date(2024, 1, 4)
    expected = [1, 1, 1]
    obtained = rc.compute_intervals([date1, date2, date3, date4])
    assert expected == obtained
