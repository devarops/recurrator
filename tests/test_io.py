import recurrator.io as io

from datetime import date
import pytest

@pytest.fixture
def csv_path():
    return "tests/data/tasks.csv"

def test_import_tasks_from_csv(csv_path):
    pass
