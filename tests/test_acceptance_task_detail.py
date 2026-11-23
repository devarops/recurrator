from datetime import date

from conftest import _complete, _copy_fixture, _read_task


def test_detail_reports_last_completion(tmp_path):
    """A read reports the fourth completion date and the later skip date."""
    csv_path = _copy_fixture(
        "tests/data/acceptance_task_detail_reports_last_completion.csv", tmp_path
    )

    response = _read_task(csv_path, 1)

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
    csv_path = _copy_fixture(
        "tests/data/acceptance_task_detail_last_completion_ignores_the_skip_date.csv",
        tmp_path,
    )

    response = _read_task(csv_path, 1)

    assert response.status_code == 200

    body = response.json()
    assert body["latest_date"] == "2025-06-15"
    assert body["latest_done_date"] == "2025-02-01"
    assert body["latest_done_date"] != body["latest_date"]
