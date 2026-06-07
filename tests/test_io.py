from datetime import date

import recurrator.io as io
from recurrator.io import Context
from conftest import (
    _get_file_checksum,
    _assert_file_unchanged,
    _verify_task_as_done,
    TASK_2_ORIGINAL_DATES,
    TASK_2_UPDATED_DATES,
    TASK_2_COMPLETION_DATE,
    TASK_2_EXPECTED_AFTER_COMPLETION,
    TASK_5_ORIGINAL_DATES,
    TASK_5_COMPLETION_DATE,
    TASK_5_EXPECTED_AFTER_COMPLETION,
)


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

    # Computed coins
    expected_coins = 14
    obtained_coins = first_task.coins
    assert obtained_coins == expected_coins


def test_import_tasks_from_csv_starred_task():
    """Verify import_tasks_from_csv computes coins correctly for a starred task."""
    csv_path = "tests/data/test_contexts.csv"
    task_list = io.import_tasks_from_csv(csv_path)

    # Find the starred task with ID 1
    task_1 = [t for t in task_list if t.id == 1][0]

    expected_starred = True
    obtained_starred = task_1.starred
    assert obtained_starred == expected_starred

    expected_recurrence_days = 21
    obtained_recurrence_days = task_1.recurrence_days
    assert obtained_recurrence_days == expected_recurrence_days

    expected_coins = 42
    obtained_coins = task_1.coins
    assert obtained_coins == expected_coins


def test_import_tasks_from_csv_two_contexts():
    """Verify import_tasks_from_csv correctly handles multiple contexts in CSV file."""
    csv_path = "tests/data/test_three_tasks.csv"
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


def test_import_dates_from_csv():
    """Verify import_dates_from_csv correctly parses dates from CSV file."""
    task_id = 2
    csv_path = "tests/data/test_three_tasks.csv"
    obtained_dates = io.import_dates_from_csv(task_id, csv_path)
    assert isinstance(obtained_dates, list)

    assert obtained_dates == TASK_2_ORIGINAL_DATES


def test_update_task_dates_in_csv():
    """Verify update_task_dates correctly writes dates to CSV file."""
    task_id = 2
    csv_path = "tests/data/test_three_tasks.csv"

    original_checksum = _get_file_checksum(csv_path)

    io.update_task_dates(task_id, TASK_2_UPDATED_DATES, csv_path)
    obtained_dates = io.import_dates_from_csv(task_id, csv_path)
    assert obtained_dates == TASK_2_UPDATED_DATES

    # Undo changes to CSV file for other tests
    io.update_task_dates(task_id, TASK_2_ORIGINAL_DATES, csv_path)
    obtained_dates = io.import_dates_from_csv(task_id, csv_path)
    assert obtained_dates == TASK_2_ORIGINAL_DATES

    _assert_file_unchanged(csv_path, original_checksum)


def test_update_task_skip_count_in_csv():
    """Verify update_task_skip_count_in_csv correctly updates skip count."""
    task_id = 2
    csv_path = "tests/data/test_three_tasks.csv"

    original_checksum = _get_file_checksum(csv_path)

    expected_skip_count = 5
    io.update_task_skip_count(task_id, expected_skip_count, csv_path)
    obtained_skip_count = io.import_tasks_from_csv(csv_path)[0].skip_count
    assert obtained_skip_count == expected_skip_count

    # Undo changes to CSV file for other tests
    original_skip_count = 10
    io.update_task_skip_count(task_id, original_skip_count, csv_path)
    obtained_skip_count = io.import_tasks_from_csv(csv_path)[0].skip_count
    assert obtained_skip_count == original_skip_count

    _assert_file_unchanged(csv_path, original_checksum)


def test_update_task_as_done_in_csv():
    """Verify update_task_as_done_in_csv correctly updates dates and skip count."""
    csv_path = "tests/data/test_three_tasks.csv"
    original_checksum = _get_file_checksum(csv_path)

    # Scenario 1: Task with partial dates (some None values)
    _verify_task_as_done(
        task_id=2,
        csv_path=csv_path,
        completion_date=TASK_2_COMPLETION_DATE,
        expected_dates=TASK_2_EXPECTED_AFTER_COMPLETION,
        original_dates=TASK_2_ORIGINAL_DATES,
    )

    # Scenario 2: Task with all dates filled
    _verify_task_as_done(
        task_id=5,
        csv_path=csv_path,
        completion_date=TASK_5_COMPLETION_DATE,
        expected_dates=TASK_5_EXPECTED_AFTER_COMPLETION,
        original_dates=TASK_5_ORIGINAL_DATES,
    )

    _assert_file_unchanged(csv_path, original_checksum)


def test_import_tasks_from_csv_latest_done_date():
    """Verify imported task has latest_done_date matching date_4 from CSV."""
    csv_path = "tests/data/test_single_task.csv"
    tasks = io.import_tasks_from_csv(csv_path)
    first_task = tasks[0]
    expected_latest_done_date = date(2025, 8, 19)
    obtained_latest_done_date = first_task.latest_done_date
    assert obtained_latest_done_date == expected_latest_done_date


def test_update_task_skip_date_in_csv():
    """Verify update_task_skip_date correctly updates skip_date in CSV."""
    task_id = 2
    csv_path = "tests/data/test_three_tasks.csv"

    original_checksum = _get_file_checksum(csv_path)

    new_skip_date = date(2026, 6, 7)
    io.update_task_skip_date(task_id, new_skip_date, csv_path)

    # Verify latest_date changed (it depends on skip_date)
    updated_task = io.get_task_by_id(task_id, csv_path)
    assert updated_task.latest_date == new_skip_date

    # Undo changes to CSV file for other tests
    original_skip_date = date(2025, 5, 2)
    io.update_task_skip_date(task_id, original_skip_date, csv_path)

    _assert_file_unchanged(csv_path, original_checksum)


def test_update_task_as_skipped_in_csv():
    """Verify update_task_as_skipped increments skip_count and updates skip_date."""
    task_id = 2
    csv_path = "tests/data/test_three_tasks.csv"

    original_checksum = _get_file_checksum(csv_path)

    original_skip_count = io.get_task_by_id(task_id, csv_path).skip_count

    new_skip_date = date(2026, 6, 7)
    io.update_task_as_skipped(task_id, new_skip_date, csv_path)

    updated_task = io.get_task_by_id(task_id, csv_path)
    expected_skip_count = original_skip_count + 1
    obtained_skip_count = updated_task.skip_count
    assert obtained_skip_count == expected_skip_count

    expected_skip_date = new_skip_date
    obtained_skip_date = updated_task.latest_date
    assert obtained_skip_date == expected_skip_date

    # Undo changes to CSV file for other tests
    io.update_task_skip_count(task_id, original_skip_count, csv_path)
    original_skip_date = date(2025, 5, 2)
    io.update_task_skip_date(task_id, original_skip_date, csv_path)

    _assert_file_unchanged(csv_path, original_checksum)
