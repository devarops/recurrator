import csv

from fastapi.testclient import TestClient
from recurrator.api import app
from conftest import THREE_TASKS_CSV, _copy_fixture

client = TestClient(app)


def _write_description(csv_path, task_id, text):
    """Write a description and check that the confirmation carries it."""
    response = client.patch(
        f"/api/task/{task_id}/description?csv={csv_path}", json={"description": text}
    )

    assert response.status_code == 200
    assert response.json() == {"id": task_id, "description": text}


def test_description_is_written_verbatim(tmp_path):
    """A written description reads back unchanged, markdown and line breaks included."""
    csv_path = _copy_fixture(THREE_TASKS_CSV, tmp_path)
    text = "Line one\n- [ ] two\n\n**bold** and _italic_"

    _write_description(csv_path, 2, text)

    assert client.get(f"/api/task/2?csv={csv_path}").json()["description"] == text

    with open(csv_path, newline="") as file:
        stored = list(csv.DictReader(file))
    assert stored[0]["description"] == text


def test_empty_description_is_rejected(tmp_path):
    """An empty or whitespace-only description is refused and the text survives."""
    csv_path = _copy_fixture(THREE_TASKS_CSV, tmp_path)
    before = client.get(f"/api/task/2?csv={csv_path}").json()["description"]

    for text in ("", "   ", "\n\t "):
        response = client.patch(
            f"/api/task/2/description?csv={csv_path}", json={"description": text}
        )

        assert response.status_code == 400
        assert "error" in response.json()

    assert client.get(f"/api/task/2?csv={csv_path}").json()["description"] == before


def test_description_unknown_task_returns_404(tmp_path):
    """A write for a missing task is refused instead of silently succeeding."""
    csv_path = _copy_fixture(THREE_TASKS_CSV, tmp_path)

    response = client.patch(f"/api/task/999/description?csv={csv_path}", json={"description": "x"})

    assert response.status_code == 404
    assert "error" in response.json()


def test_description_whitespace_is_preserved(tmp_path):
    """Padded text survives the write and comes back from a later read."""
    csv_path = _copy_fixture(THREE_TASKS_CSV, tmp_path)
    text = "\t  Buy milk\n- [ ] eggs  \t\n"

    _write_description(csv_path, 2, text)

    stored = client.get(f"/api/task/2?csv={csv_path}")

    assert stored.status_code == 200
    assert stored.json()["description"] == text
