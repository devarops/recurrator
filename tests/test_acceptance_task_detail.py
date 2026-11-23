from datetime import date

from conftest import _complete, _copy_fixture, _read_task


def _read_copied_task(fixture, tmp_path):
    """Copy a task fixture and read its first task."""
    return _read_task(_copy_fixture(fixture, tmp_path), 1)


def test_detail_reports_last_completion(tmp_path):
    """A read reports the fourth completion date and the later skip date."""
    response = _read_copied_task(
        "tests/data/acceptance_task_detail_reports_last_completion.csv", tmp_path
    )

    assert response.status_code == 200

    body = response.json()
    assert body["latest_done_date"] == "2025-05-02"
    assert body["latest_date"] == "2025-07-01"


def test_completion_returns_last_completion(tmp_path):
    """A completion response reports the completion date as the last completion."""
    csv_path = _copy_fixture(
        "tests/data/acceptance_task_detail_reports_last_completion.csv", tmp_path
    )

    response = _complete(csv_path, 1)

    assert response.status_code == 200

    assert response.json()["latest_done_date"] == date.today().isoformat()


def test_last_completion_ignores_the_skip_date(tmp_path):
    """A later skip date moves latest_date without moving latest_done_date."""
    response = _read_copied_task(
        "tests/data/acceptance_task_detail_last_completion_ignores_the_skip_date.csv",
        tmp_path,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["latest_date"] == "2025-06-15"
    assert body["latest_done_date"] == "2025-02-01"
    assert body["latest_done_date"] != body["latest_date"]


def test_detail_reports_a_single_context_array(tmp_path):
    """A task in one context reports a one-element contexts array."""
    response = _read_copied_task(
        "tests/data/acceptance_task_detail_reports_a_single_context_array.csv", tmp_path
    )

    assert response.status_code == 200

    contexts = response.json()["contexts"]
    assert contexts == ["chores"]


def test_detail_reports_multiple_contexts(tmp_path):
    """A task in several contexts reports them sorted and deduplicated."""
    response = _read_copied_task(
        "tests/data/acceptance_task_detail_reports_multiple_contexts.csv", tmp_path
    )

    assert response.status_code == 200

    contexts = response.json()["contexts"]
    assert contexts == ["casa", "chores", "work"]
