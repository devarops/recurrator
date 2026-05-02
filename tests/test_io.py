import pytest
from datetime import date

import recurrator.io as io
from recurrator.io import Context


@pytest.fixture
def csv_path():
    """Path to test CSV file with one task record."""
    return "tests/data/test_single_task.csv"


def test_import_tasks_from_csv(csv_path):
    """Verify import_tasks_from_csv returns valid task from CSV file."""
    task_list = io.import_tasks_from_csv(csv_path)
    assert isinstance(task_list, list)
    expected_list_length = 1
    obtained_list_length = len(task_list)
    assert obtained_list_length == expected_list_length
    first_task = task_list[0]
    expected_id = 8
    obtained_id = first_task.id
    assert obtained_id == expected_id
    expected_description = "TypeLit.io"
    obtained_description = first_task.description
    assert obtained_description == expected_description
    assert isinstance(first_task.context, Context)
    expected_skip_count = 1
    obtained_skip_count = first_task.skip_count
    assert obtained_skip_count == expected_skip_count
    expected_starred = False
    obtained_starred = first_task.starred
    assert obtained_starred == expected_starred
    expected_latest_date = date(2025, 11, 17)
    obtained_latest_date = first_task.latest_date
    assert obtained_latest_date == expected_latest_date
