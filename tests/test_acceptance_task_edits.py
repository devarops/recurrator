import csv

from fastapi.testclient import TestClient
from recurrator.api import app
from conftest import _copy_fixture

client = TestClient(app)

FIXTURE = "tests/data/test_three_tasks.csv"


def test_description_is_written_verbatim(tmp_path):
    """A written description reads back unchanged, markdown and line breaks included."""
    csv_path = _copy_fixture(FIXTURE, tmp_path)
    text = "Line one\n- [ ] two\n\n**bold** and _italic_"

    response = client.patch(f"/task/2/description?csv={csv_path}", json={"description": text})

    assert response.status_code == 200
    assert response.json() == {"id": 2, "description": text}

    assert client.get(f"/task/2?csv={csv_path}").json()["description"] == text

    with open(csv_path, newline="") as file:
        stored = list(csv.DictReader(file))
    assert stored[0]["description"] == text
