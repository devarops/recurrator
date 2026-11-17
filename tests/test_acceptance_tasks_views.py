from conftest import _read_task_ids


def test_all_tasks_are_listed():
    """The collection lists every ID in file order, including the future task."""
    response = _read_task_ids("tests/data/acceptance_tasks_views_all_tasks.csv")

    assert response.status_code == 200

    assert response.json() == [7, 2, 9]
