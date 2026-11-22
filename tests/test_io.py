from datetime import date
from pathlib import Path

import pytest

import recurrator.io as io
from conftest import (
    _get_file_checksum,
    _assert_file_unchanged,
    _restore_completion_fields,
    CONTEXT_TASKS_CSV,
    GLICKO_CONTRACT_CSV,
    SINGLE_TASK_CSV,
    THREE_TASKS_CSV,
    TWO_RATINGS_CSV,
    TASK_2_ORIGINAL_DATES,
    TASK_2_ORIGINAL_SKIP_COUNT,
    TASK_2_ORIGINAL_SKIP_DATE,
    TASK_2_UPDATED_DATES,
    TASK_2_COMPLETION_DATE,
    TASK_2_EXPECTED_AFTER_COMPLETION,
    TASK_5_ORIGINAL_DATES,
    TASK_5_COMPLETION_DATE,
    TASK_5_EXPECTED_AFTER_COMPLETION,
)


def test_import_tasks_from_csv_single_task():
    """Verify import_tasks_from_csv returns valid task from CSV file."""
    csv_path = SINGLE_TASK_CSV
    task_list = io.import_tasks_from_csv(csv_path)

    # Returns a list with one Task
    assert isinstance(task_list, list)
    assert len(task_list) == 1

    first_task = task_list[0]

    # Basic attributes from CSV
    assert first_task.id == 8
    assert first_task.description == "TypeLit.io"
    assert first_task.contexts == ["laptop"]
    assert first_task.skip_count == 1
    assert first_task.starred is False

    # Computed attributes
    assert first_task.latest_date == date(2025, 11, 17)
    assert first_task.recurrence_days == 14
    assert first_task.due_date == date(2025, 12, 1)

    # Computed coins
    assert first_task.coins == 14


def test_import_tasks_from_csv_starred_task():
    """Verify import_tasks_from_csv computes coins correctly for a starred task."""
    csv_path = CONTEXT_TASKS_CSV
    task_list = io.import_tasks_from_csv(csv_path)

    # Find the starred task with ID 1
    task_1 = [t for t in task_list if t.id == 1][0]

    assert task_1.starred is True
    assert task_1.recurrence_days == 21
    assert task_1.coins == 42


def test_import_dates_from_csv():
    """Verify import_dates_from_csv correctly parses dates from CSV file."""
    task_id = 2
    csv_path = THREE_TASKS_CSV
    obtained_dates = io.import_dates_from_csv(task_id, csv_path)
    assert isinstance(obtained_dates, list)

    assert obtained_dates == TASK_2_ORIGINAL_DATES


def test_update_task_dates_in_csv():
    """Verify update_task_dates correctly writes dates to CSV file."""
    task_id = 2
    csv_path = THREE_TASKS_CSV

    original_checksum = _get_file_checksum(csv_path)

    io.update_task_dates(task_id, TASK_2_UPDATED_DATES, csv_path)
    assert io.import_dates_from_csv(task_id, csv_path) == TASK_2_UPDATED_DATES

    # Undo changes to CSV file for other tests
    io.update_task_dates(task_id, TASK_2_ORIGINAL_DATES, csv_path)
    assert io.import_dates_from_csv(task_id, csv_path) == TASK_2_ORIGINAL_DATES

    _assert_file_unchanged(csv_path, original_checksum)


def test_update_task_skip_count_in_csv():
    """Verify update_task_skip_count_in_csv correctly updates skip count."""
    task_id = 2
    csv_path = THREE_TASKS_CSV

    original_checksum = _get_file_checksum(csv_path)

    io.update_task_skip_count(task_id, 5, csv_path)
    assert io.import_tasks_from_csv(csv_path)[0].skip_count == 5

    # Undo changes to CSV file for other tests
    io.update_task_skip_count(task_id, TASK_2_ORIGINAL_SKIP_COUNT, csv_path)
    assert io.import_tasks_from_csv(csv_path)[0].skip_count == TASK_2_ORIGINAL_SKIP_COUNT

    _assert_file_unchanged(csv_path, original_checksum)


def test_write_preserves_quotes_in_description():
    """Verify an unrelated write leaves a quoted description intact."""
    task_id = 1
    csv_path = "tests/data/test_quoted_description.csv"
    original_checksum = _get_file_checksum(csv_path)

    io.update_task_skip_count(task_id, 3, csv_path)
    assert io.get_task_by_id(task_id, csv_path).description == 'He said "hola" once, and left.'

    io.update_task_skip_count(task_id, 0, csv_path)
    _assert_file_unchanged(csv_path, original_checksum)


def test_failed_write_leaves_the_file_unchanged(monkeypatch):
    """Verify a write that fails partway does not touch the stored file."""
    csv_path = THREE_TASKS_CSV
    original_checksum = _get_file_checksum(csv_path)
    calls = {"count": 0}

    def failing_formatter(fieldnames, row):
        calls["count"] += 1
        if calls["count"] == 2:
            raise RuntimeError("write failed")
        return io._format_csv_line(fieldnames, row)

    monkeypatch.setattr(io, "_format_csv_line", failing_formatter)
    with pytest.raises(RuntimeError):
        io.update_task_skip_count(2, 5, csv_path)

    _assert_file_unchanged(csv_path, original_checksum)
    assert not Path(csv_path + ".tmp").exists()


def _verify_task_as_done(
    task_id: int,
    csv_path: str,
    completion_date: date,
    expected_dates: list,
    original_dates: list,
) -> None:
    """Verify and undo task completion scenario.

    Args:
        task_id: ID of the task to test
        csv_path: Path to CSV file
        completion_date: Date the task was marked as done
        expected_dates: Expected dates after completion
        original_dates: Original dates to restore after test
    """
    original_task = io.get_task_by_id(task_id, csv_path)
    original_skip_count = original_task.skip_count

    io.update_task_as_done(task_id, completion_date, csv_path)
    assert io.get_task_by_id(task_id, csv_path).skip_count == 0

    assert io.import_dates_from_csv(task_id, csv_path) == expected_dates

    _restore_completion_fields(task_id, original_skip_count, original_dates, csv_path)


def test_update_task_as_done_in_csv():
    """Verify update_task_as_done_in_csv correctly updates dates and skip count."""
    csv_path = THREE_TASKS_CSV
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
    csv_path = SINGLE_TASK_CSV
    tasks = io.import_tasks_from_csv(csv_path)
    first_task = tasks[0]

    assert first_task.latest_done_date == date(2025, 8, 19)


def test_update_task_skip_date_in_csv():
    """Verify update_task_skip_date correctly updates skip_date in CSV."""
    task_id = 2
    csv_path = THREE_TASKS_CSV

    original_checksum = _get_file_checksum(csv_path)

    new_skip_date = date(2026, 6, 7)
    io.update_task_skip_date(task_id, new_skip_date, csv_path)

    # Verify latest_date changed (it depends on skip_date)
    updated_task = io.get_task_by_id(task_id, csv_path)
    assert updated_task.latest_date == new_skip_date

    # Undo changes to CSV file for other tests
    io.update_task_skip_date(task_id, TASK_2_ORIGINAL_SKIP_DATE, csv_path)

    _assert_file_unchanged(csv_path, original_checksum)


def test_update_task_as_skipped_in_csv():
    """Verify update_task_as_skipped increments skip_count and updates skip_date."""
    task_id = 2
    csv_path = THREE_TASKS_CSV

    original_checksum = _get_file_checksum(csv_path)

    original_skip_count = io.get_task_by_id(task_id, csv_path).skip_count

    new_skip_date = date(2026, 6, 7)
    io.update_task_as_skipped(task_id, new_skip_date, csv_path)

    updated_task = io.get_task_by_id(task_id, csv_path)
    assert updated_task.skip_count == original_skip_count + 1
    assert updated_task.latest_date == new_skip_date

    # Undo changes to CSV file for other tests
    io.update_task_skip_count(task_id, original_skip_count, csv_path)
    io.update_task_skip_date(task_id, TASK_2_ORIGINAL_SKIP_DATE, csv_path)

    _assert_file_unchanged(csv_path, original_checksum)


def test_import_tasks_from_csv_rating():
    """Verify import_tasks_from_csv reads the task rating as an integer."""
    csv_path = GLICKO_CONTRACT_CSV
    task_list = io.import_tasks_from_csv(csv_path)

    assert task_list[0].rating == 1500


def test_import_tasks_from_csv_rating_deviation():
    """Verify import_tasks_from_csv reads the task rating deviation as an integer."""
    csv_path = GLICKO_CONTRACT_CSV
    task_list = io.import_tasks_from_csv(csv_path)

    assert task_list[0].rating_deviation == 350


def test_update_task_rating_date_in_csv():
    """Verify update_task_rating_date writes and restores the rating anchor."""
    task_id = 1
    csv_path = TWO_RATINGS_CSV

    original_checksum = _get_file_checksum(csv_path)
    original_task = io.get_task_by_id(task_id, csv_path)

    new_rating_date = date(2026, 11, 8)
    io.update_task_rating_date(task_id, new_rating_date, csv_path)
    assert io.get_task_by_id(task_id, csv_path).rating_date == new_rating_date

    io.update_task_rating_date(task_id, original_task.rating_date, csv_path)
    assert io.get_task_by_id(task_id, csv_path).rating_date == original_task.rating_date

    _assert_file_unchanged(csv_path, original_checksum)


def _assert_contexts_csv_rejected(tmp_path, *rows, header="id,display_name,description,scopes"):
    """Write a context file with the header and rows and assert the reader rejects it."""
    csv_path = tmp_path / "contexts.csv"
    body = "\n".join(rows)
    csv_path.write_text(f"{header}\n{body}\n")

    with pytest.raises(ValueError):
        io.import_contexts_from_csv(csv_path)


def test_import_contexts_from_csv_rejects_empty_scopes(tmp_path):
    """Verify the reader refuses a context with an empty scopes array."""
    _assert_contexts_csv_rejected(tmp_path, "casa,Home,Home projects.,[]")


def test_import_contexts_from_csv_rejects_empty_display_name(tmp_path):
    """Verify the reader refuses a context with an empty display name."""
    _assert_contexts_csv_rejected(tmp_path, 'casa,,Home projects.,"[""personal""]"')


def test_import_contexts_from_csv_rejects_empty_id(tmp_path):
    """Verify the reader refuses a context with an empty id."""
    _assert_contexts_csv_rejected(tmp_path, ',Home,Home projects.,"[""personal""]"')


def test_import_contexts_from_csv_rejects_empty_description(tmp_path):
    """Verify the reader refuses a context with an empty description."""
    _assert_contexts_csv_rejected(tmp_path, 'casa,Home,,"[""personal""]"')


def test_import_contexts_from_csv_rejects_duplicate_ids(tmp_path):
    """Verify the reader refuses two contexts with the same id."""
    _assert_contexts_csv_rejected(
        tmp_path,
        'casa,Home,Home projects.,"[""personal""]"',
        'casa,Garden,Garden projects.,"[""work""]"',
    )


def test_import_contexts_from_csv_rejects_missing_display_name_column(tmp_path):
    """Verify the reader refuses a context file without a display name column."""
    _assert_contexts_csv_rejected(
        tmp_path,
        'casa,Home projects.,"[""personal""]"',
        header="id,description,scopes",
    )


def test_import_contexts_from_csv_rejects_missing_scopes_column(tmp_path):
    """Verify the reader refuses a context file without a scopes column."""
    _assert_contexts_csv_rejected(
        tmp_path,
        "casa,Home,Home projects.",
        header="id,display_name,description",
    )


def test_import_contexts_from_csv_rejects_blank_display_name(tmp_path):
    """Verify the reader refuses a context whose display name is only whitespace."""
    _assert_contexts_csv_rejected(tmp_path, 'casa,   ,Home projects.,"[""personal""]"')


def test_import_contexts_from_csv_rejects_id_with_slash(tmp_path):
    """Verify the reader refuses a context id that spans path segments."""
    _assert_contexts_csv_rejected(tmp_path, 'ca/sa,Home,Home projects.,"[""personal""]"')
