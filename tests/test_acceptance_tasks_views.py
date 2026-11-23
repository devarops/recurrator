from conftest import _copy_fixture, _read_due_task_ids, _read_task, _read_task_ids

TASKS_VIEWS_CSV = "tests/data/acceptance_tasks_views_all_tasks.csv"


def test_all_tasks_are_listed():
    """The collection lists every ID in file order, including the future task."""
    response = _read_task_ids(TASKS_VIEWS_CSV)

    assert response.status_code == 200

    assert response.json() == [7, 2, 9]


def test_due_tasks_are_listed_for_a_date():
    """A dated due read returns the due IDs and excludes the later task."""
    response = _read_due_task_ids(TASKS_VIEWS_CSV, "2026-01-01")

    assert response.status_code == 200

    assert response.json() == [7, 9]


def test_no_context_due_read_is_read_only(tmp_path):
    """A due read without a context writes no skip count or skip date."""
    csv_path = _copy_fixture(TASKS_VIEWS_CSV, tmp_path)

    def state(task_id):
        task = _read_task(csv_path, task_id).json()
        return task["skip_count"], task["due_date"]

    before = {task_id: state(task_id) for task_id in (7, 2, 9)}

    response = _read_due_task_ids(csv_path, "2026-01-01")

    assert response.status_code == 200

    assert response.json() == [7, 9]
    assert {task_id: state(task_id) for task_id in (7, 2, 9)} == before
