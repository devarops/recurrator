def test_accent_for_is_stable(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("index.html", csv_path, date="2026-05-01"))

    assert page.evaluate("ui.accentFor('activity')") == "green"
    assert page.evaluate("ui.accentFor('chores')") == "orange"
    assert page.evaluate("ui.accentFor('casa')") == "green"
    assert page.evaluate("ui.accentFor('laptop')") == "purple"
    assert page.evaluate("ui.accentFor('lectura')") == "aqua"


def test_monster_title_takes_three_words(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("index.html", csv_path, date="2026-05-01"))

    title = page.evaluate("ui.monsterTitle('Recoger basura de los tambos de afuera')")
    assert title == "Recoger basura de"
    assert page.evaluate("ui.monsterTitle('**Bold** start of a line')") == "Bold start of"
    assert page.evaluate("ui.monsterTitle('- [ ] Encimera')") == "Encimera"
    assert page.evaluate("ui.monsterTitle('Limpiar refri')") == "Limpiar refri"


def test_due_state_boundaries(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("index.html", csv_path, date="2026-05-01"))

    assert page.evaluate("ui.dueState({due_date: '2026-05-01', today: '2026-05-01'})") == "due"
    assert page.evaluate("ui.dueState({due_date: '2026-05-02', today: '2026-05-01'})") == "not-due"
    assert page.evaluate("ui.dueState({})") == ""


def test_render_markdown_constructs(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("index.html", csv_path, date="2026-05-01"))

    rendered = page.evaluate(
        "ui.renderMarkdown('**bold** _italic_ `code` [link](https://example.com)')"
    )
    assert "<strong>bold</strong>" in rendered
    assert "<em>italic</em>" in rendered
    assert "<code>code</code>" in rendered
    assert 'target="_blank"' in rendered
    assert 'rel="noopener noreferrer"' in rendered

    lists = page.evaluate(r"ui.renderMarkdown('- one\n- two')")
    assert "<ul>" in lists
    assert "<li>one</li>" in lists

    checks = page.evaluate(r"ui.renderMarkdown('- [ ] open\n- [x] done')")
    assert 'type="checkbox"' in checks
    assert "checked" in checks

    breaks = page.evaluate(r"ui.renderMarkdown('first\nsecond')")
    assert "<br>" in breaks


def test_render_markdown_escapes_html(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("index.html", csv_path, date="2026-05-01"))

    rendered = page.evaluate("ui.renderMarkdown('<script>alert(1)</script>')")
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered


def test_render_scope_tile_shows_more_line(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("index.html", csv_path, date="2026-05-01"))

    rendered = page.evaluate("""ui.renderScopeTile({
            scope: 'all',
            label: 'All',
            emoji: '🗂️',
            dueCount: 6,
            names: ['a', 'b', 'c', 'd'],
            href: '#'
        })""")
    assert "+2 more" in rendered


def test_render_markdown_single_line_break(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("index.html", csv_path, date="2026-05-01"))

    rendered = page.evaluate("ui.renderMarkdown('first\\nsecond')")
    assert rendered == "<p>first<br>second</p>"


def test_render_markdown_paragraph_break(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("index.html", csv_path, date="2026-05-01"))

    rendered = page.evaluate("ui.renderMarkdown('first\\n\\nsecond')")
    assert rendered == "<p>first</p><p>second</p>"


def test_render_markdown_leaves_a_literal_escape_alone(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("index.html", csv_path, date="2026-05-01"))

    rendered = page.evaluate("ui.renderMarkdown(String.raw`first\\nsecond`)")
    assert rendered == "<p>first\\nsecond</p>"
