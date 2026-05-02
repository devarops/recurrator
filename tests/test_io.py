import pytest

import recurrator.io as io


@pytest.fixture
def csv_path():
    return "tests/data/test_single_task.csv"


def test_import_tasks_from_csv(csv_path):
    task_list = io.import_tasks_from_csv(csv_path)
    assert isinstance(task_list, list)
    expected_list_length = 1
    obteined_list_length = len(task_list)
    assert obteined_list_length == expected_list_length
