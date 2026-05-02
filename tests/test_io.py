import pytest


@pytest.fixture
def path():
    return "tests/data/test_single_task.csv"


def test_import_tasks_from_csv(path):
    pass
