import os

PUBLIC_DIR = "public"

HTML_FILES = {
    "index.html": [
        '<div id="contexts">',
        '<div id="error"',
        '<script src="main.js">',
        "<title>Recurrator</title>",
    ],
    "context.html": [
        '<div id="tasks">',
        '<div id="error"',
        '<script src="main.js">',
        '<h2 id="contextName">',
    ],
    "task.html": [
        '<div id="task">',
        '<div id="error"',
        '<script src="main.js">',
        '<a id="contextLink"',
    ],
}


def test_html_files_have_expected_structure():
    """Verify each HTML file exists and contains expected DOM landmarks."""
    for filename, expected_markers in HTML_FILES.items():
        filepath = os.path.join(PUBLIC_DIR, filename)
        assert os.path.exists(filepath), f"Missing {filepath}"
        with open(filepath) as f:
            content = f.read()
        for marker in expected_markers:
            assert marker in content, f"{filename} missing expected element: {marker}"
