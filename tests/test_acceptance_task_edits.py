import csv

from conftest import (
    THREE_TASKS_CSV,
    _assert_error_response,
    _copy_fixture,
    _patch_description,
    _patch_description_body,
    _read_task,
)


def _assert_description_written(csv_path, task_id, text):
    """Send a description and check that the confirmation carries it."""
    response = _patch_description(csv_path, task_id, text)

    assert response.status_code == 200
    assert response.json() == {"id": task_id, "description": text}


def _assert_description_reads_back(csv_path, task_id, text):
    """Write a description and check that a later read returns it."""
    _assert_description_written(csv_path, task_id, text)

    response = _read_task(csv_path, task_id)

    assert response.status_code == 200
    assert response.json()["description"] == text


def test_description_is_written_verbatim(tmp_path):
    """A written description reads back unchanged, markdown and line breaks included."""
    csv_path = _copy_fixture(THREE_TASKS_CSV, tmp_path)
    text = "Line one\n- [ ] two\n\n**bold** and _italic_"

    _assert_description_reads_back(csv_path, 2, text)

    with open(csv_path, newline="") as file:
        stored = list(csv.DictReader(file))
    assert stored[0]["description"] == text


def test_empty_description_is_rejected(tmp_path):
    """An empty or whitespace-only description is refused and the text survives."""
    csv_path = _copy_fixture(THREE_TASKS_CSV, tmp_path)
    before = _read_task(csv_path, 2).json()["description"]

    for text in ("", "   ", "\n\t "):
        response = _patch_description(csv_path, 2, text)

        _assert_error_response(response, 400)

    assert _read_task(csv_path, 2).json()["description"] == before


def test_description_unknown_task_returns_404(tmp_path):
    """A write for a missing task is refused instead of silently succeeding."""
    csv_path = _copy_fixture(THREE_TASKS_CSV, tmp_path)

    response = _patch_description(csv_path, 999, "x")

    _assert_error_response(response, 404)


def test_description_whitespace_is_preserved(tmp_path):
    """Padded text survives the write and comes back from a later read."""
    csv_path = _copy_fixture(THREE_TASKS_CSV, tmp_path)
    text = "\t  Buy milk\n- [ ] eggs  \t\n"

    _assert_description_reads_back(csv_path, 2, text)


def test_backslash_and_n_are_ordinary_text(tmp_path):
    """A backslash and an n are stored as two characters, not as a line break."""
    csv_path = _copy_fixture(THREE_TASKS_CSV, tmp_path)
    text = "one\\ntwo"

    _assert_description_reads_back(csv_path, 2, text)


def test_unknown_task_takes_precedence_over_an_empty_description(tmp_path):
    """A missing task answers 404 before the text is refused."""
    csv_path = _copy_fixture(THREE_TASKS_CSV, tmp_path)

    for text in ("", "   ", "\n\t "):
        response = _patch_description(csv_path, 999, text)

        _assert_error_response(response, 404)


def test_malformed_description_body_is_rejected(tmp_path):
    """A body without the text, or with a non-string, is refused."""
    csv_path = _copy_fixture(THREE_TASKS_CSV, tmp_path)
    previous = _read_task(csv_path, 2).json()["description"]

    for payload in ({}, {"description": 123}, {"description": None}):
        response = _patch_description_body(csv_path, 2, payload)

        _assert_error_response(response, 422)

    assert _read_task(csv_path, 2).json()["description"] == previous
