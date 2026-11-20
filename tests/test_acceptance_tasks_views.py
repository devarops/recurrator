from conftest import _read_due_task_ids, _read_task_ids

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
