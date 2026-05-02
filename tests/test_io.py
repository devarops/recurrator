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

    # Returns a list with one Task
    assert isinstance(task_list, list)
    assert len(task_list) == 1

    task = task_list[0]

    # Basic attributes from CSV
    assert task.id == 8
    assert task.description == "TypeLit.io"
    assert isinstance(task.context, Context)
    assert task.skip_count == 1
    assert task.starred is False

    # Computed attributes
    assert task.latest_date == date(2025, 11, 17)
    assert task.recurrence_days == 14
