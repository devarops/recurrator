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


def test_import_dates_from_csv():
    """Verify import_dates_from_csv correctly parses dates from CSV file."""
    task_id = 2
    csv_path = "tests/data/test_two_contexts.csv"
    obtained_dates = io.import_dates_from_csv(task_id, csv_path)
    assert isinstance(obtained_dates, list)

    expected_dates = [
        None,
        None,
        date(2024, 1, 8),
        date(2024, 12, 7),
    ]
    assert obtained_dates == expected_dates


def test_update_task_dates_in_csv():
    """Verify update_task_dates_in_csv correctly writes dates to CSV file."""
    import hashlib

    task_id = 2
    csv_path = "tests/data/test_two_contexts.csv"

    # Capture checksum before test
    with open(csv_path, "rb") as f:
        original_checksum = hashlib.md5(f.read()).hexdigest()

    expected_dates = [
        None,
        None,
        date(2025, 2, 1),
        date(2025, 11, 2),
    ]
    io.update_task_dates_in_csv(task_id, expected_dates, csv_path)
    obtained_dates = io.import_dates_from_csv(task_id, csv_path)
    assert obtained_dates == expected_dates

    # Undo changes to CSV file for other tests
    original_dates = [
        None,
        None,
        date(2024, 1, 8),
        date(2024, 12, 7),
    ]
    io.update_task_dates_in_csv(task_id, original_dates, csv_path)
    obtained_dates = io.import_dates_from_csv(task_id, csv_path)
    assert obtained_dates == original_dates

    # Verify CSV file is unchanged after undo (no invisible modifications)
    with open(csv_path, "rb") as f:
        final_checksum = hashlib.md5(f.read()).hexdigest()
    assert final_checksum == original_checksum, "CSV was modified after undo"


def test_update_task_skip_count_in_csv():
    """Verify update_task_skip_count_in_csv correctly updates skip count."""
    import hashlib

    task_id = 2
    csv_path = "tests/data/test_two_contexts.csv"

    # Capture checksum before test
    with open(csv_path, "rb") as f:
        original_checksum = hashlib.md5(f.read()).hexdigest()

    expected_skip_count = 5
    io.update_task_skip_count(task_id, expected_skip_count, csv_path)
    obtained_skip_count = io.import_tasks_from_csv(csv_path)[0].skip_count
    assert obtained_skip_count == expected_skip_count

    # Undo changes to CSV file for other tests
    original_skip_count = 10
    io.update_task_skip_count(task_id, original_skip_count, csv_path)
    obtained_skip_count = io.import_tasks_from_csv(csv_path)[0].skip_count
    assert obtained_skip_count == original_skip_count

    # Verify CSV file is unchanged after undo (no invisible modifications)
    with open(csv_path, "rb") as f:
        final_checksum = hashlib.md5(f.read()).hexdigest()
    assert final_checksum == original_checksum, "CSV was modified after undo"


def test_update_task_as_done_in_csv():
    """Verify update_task_as_done_in_csv correctly updates dates and skip count."""
    import hashlib

    task_id = 2
    csv_path = "tests/data/test_two_contexts.csv"
    completion_date = date(2025, 2, 28)

    # Capture checksum before test
    with open(csv_path, "rb") as f:
        original_checksum = hashlib.md5(f.read()).hexdigest()

    expected_skip_count = 0
    io.update_task_as_done(task_id, completion_date, csv_path)
    obtained_skip_count = io.import_tasks_from_csv(csv_path)[0].skip_count
    assert obtained_skip_count == expected_skip_count

    expected_dates = [
        None,
        date(2024, 1, 8),
        date(2024, 12, 7),
        date(2025, 2, 28),
    ]
    obtained_dates = io.import_dates_from_csv(task_id, csv_path)
    assert obtained_dates == expected_dates

    # Undo changes to CSV file for other tests
    original_skip_count = 10
    io.update_task_skip_count(task_id, original_skip_count, csv_path)
    obtained_skip_count = io.import_tasks_from_csv(csv_path)[0].skip_count
    assert obtained_skip_count == original_skip_count
    original_dates = [
        None,
        None,
        date(2024, 1, 8),
        date(2024, 12, 7),
    ]
    io.update_task_dates_in_csv(task_id, original_dates, csv_path)
    obtained_dates = io.import_dates_from_csv(task_id, csv_path)
    assert obtained_dates == original_dates

    # Verify CSV file is unchanged after undo (no invisible modifications)
    with open(csv_path, "rb") as f:
        final_checksum = hashlib.md5(f.read()).hexdigest()
    assert final_checksum == original_checksum, "CSV was modified after undo"
