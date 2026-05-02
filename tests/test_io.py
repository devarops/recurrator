import pytest

import recurrator.io as io


@pytest.fixture
def csv_path():
    return "tests/data/test_single_task.csv"


def test_import_tasks_from_csv(csv_path):
    task_list = io.import_tasks_from_csv(csv_path)
    assert isinstance(task_list, list)
    expected_list_length = 1
    obtained_list_length = len(task_list)
    assert obtained_list_length == expected_list_length
    first_task = task_list[0]
    expected_id = 8
    obtained_id = first_task.id
    assert obtained_id == expected_id
    expected_description = "TypeLit.io"
    obtained_description = first_task.description
    assert obtained_description == expected_description
