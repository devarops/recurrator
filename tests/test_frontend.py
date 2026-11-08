import re
from pathlib import Path

PUBLIC_DIR = next(
    parent / "public"
    for parent in Path(__file__).resolve().parents
    if (parent / "public" / "index.html").is_file()
)

HTML_FILES = {
    "index.html": [
        '<div id="scopes"',
        '<article id="error"',
        '<script src="ui.js">',
        '<script src="main.js">',
        '<meta name="viewport"',
        "<title>Recurrator</title>",
    ],
    "scope.html": [
        '<div id="contexts">',
        '<article id="error"',
        '<script src="ui.js">',
        '<script src="main.js">',
        '<meta name="viewport"',
        "<title>Recurrator</title>",
    ],
    "context.html": [
        '<div id="tasks">',
        '<article id="error"',
        '<script src="ui.js">',
        '<script src="main.js">',
        '<meta name="viewport"',
        "<title>Recurrator</title>",
    ],
    "task.html": [
        '<div id="task">',
        '<article id="error"',
        '<script src="ui.js">',
        '<script src="main.js">',
        '<meta name="viewport"',
        "<title>Recurrator</title>",
    ],
}

UI_FUNCTIONS = [
    "renderScopeTile",
    "renderScopeGrid",
    "renderTaskList",
    "renderMonsterCard",
    "renderMarkdown",
    "renderSkeleton",
    "renderEmpty",
    "renderError",
    "accentFor",
    "monsterTitle",
    "dueState",
]


def test_html_files_have_expected_structure():
    """Verify each HTML file exists and contains expected DOM landmarks."""
    for filename, expected_markers in HTML_FILES.items():
        filepath = PUBLIC_DIR / filename
        assert filepath.exists(), f"Missing {filepath}"
        with open(filepath) as f:
            content = f.read()
        for marker in expected_markers:
            assert marker in content, f"{filename} missing expected element: {marker}"


def test_pages_load_styles_and_scripts_in_order():
    """Verify every page loads the three styles before the two scripts."""
    order = [
        "styles/tokens.css",
        "styles/components.css",
        "styles/pages.css",
        "ui.js",
        "main.js",
    ]
    for filename in HTML_FILES:
        content = (PUBLIC_DIR / filename).read_text()
        positions = [content.index(marker) for marker in order]
        assert positions == sorted(positions), f"{filename} loads assets out of order"


def test_pages_do_not_load_external_assets():
    """Verify no page depends on a CDN or a remote font."""
    for filename in HTML_FILES:
        content = (PUBLIC_DIR / filename).read_text()
        assert "cdn.jsdelivr.net" not in content
        assert "picocss" not in content


def test_ui_exposes_the_render_contract():
    """Verify ui.js defines the functions main.js delegates to."""
    content = (PUBLIC_DIR / "ui.js").read_text()
    for name in UI_FUNCTIONS:
        assert f"function {name}(" in content, f"ui.js missing {name}"
        assert f"{name}: {name}" in content, f"ui.js does not export {name}"


def test_colour_lives_only_in_tokens():
    """Verify components and pages reference tokens instead of literal hex colours."""
    for filename in ["components.css", "pages.css"]:
        content = (PUBLIC_DIR / "styles" / filename).read_text()
        assert not re.search(r"#[0-9a-fA-F]{3,8}\b", content), f"{filename} contains a hex colour"


def test_placeholder_and_styleguide_exist():
    """Verify the placeholder artwork and the styleguide are present."""
    assert (PUBLIC_DIR / "monster-placeholder.png").is_file()
    assert (PUBLIC_DIR / "styleguide.html").is_file()


def test_main_js_reads_the_pinned_date():
    """Verify the frontend clock accepts the date query parameter used by captures."""
    content = (PUBLIC_DIR / "main.js").read_text()
    assert "get('date')" in content


def test_main_js_reads_the_inert_scope_parameter():
    """Verify the scope parameter is read even though it does not filter yet."""
    content = (PUBLIC_DIR / "main.js").read_text()
    assert "get('scope')" in content
    assert "SCOPES_ACTIVE = false" in content
