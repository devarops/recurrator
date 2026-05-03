import pytest
from datetime import date

import recurrator.io as io
from recurrator.io import Context


def test_import_tasks_from_csv_single_task():
    """Verify import_tasks_from_csv returns valid task from CSV file."""
    csv_path = "tests/data/test_single_task.csv"
    task_list = io.import_tasks_from_csv(csv_path)

    # Returns a list with one Task
    assert isinstance(task_list, list)
    expected_list_length = 1
    obtained_list_length = len(task_list)
    assert obtained_list_length == expected_list_length

    first_task = task_list[0]

    # Basic attributes from CSV
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

    # Computed attributes
    expected_latest_date = date(2025, 11, 17)
    obtained_latest_date = first_task.latest_date
    assert obtained_latest_date == expected_latest_date

    expected_recurrence_days = 14
    obtained_recurrence_days = first_task.recurrence_days
    assert obtained_recurrence_days == expected_recurrence_days

    expected_due_date = date(2025, 12, 1)
    obtained_due_date = first_task.due_date
    assert obtained_due_date == expected_due_date


def test_import_tasks_from_csv_two_contexts():
    """Verify import_tasks_from_csv correctly handles multiple contexts in CSV file."""
    csv_path = "tests/data/test_two_contexts.csv"
    task_list = io.import_tasks_from_csv(csv_path)

    # Returns a list with three Tasks
    assert isinstance(task_list, list)
    expected_list_length = 3
    obtained_list_length = len(task_list)
    assert obtained_list_length == expected_list_length

    last_task_index = len(task_list) - 1
    last_task = task_list[last_task_index]

    # Basic attributes from CSV
    expected_id = 5
    obtained_id = last_task.id
    assert obtained_id == expected_id
