def test_all_tile_shows_due_contexts(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("index.html", csv_path, date="2026-05-01"))

    assert page.locator("#scopes .tile").count() == 4

    all_tile = page.locator("#scopes .tile", has_text="All")
    assert "3 contexts due" in all_tile.inner_text()
    assert all_tile.locator(".tile__name").all_inner_texts() == ["casa", "chores", "laptop"]

    for label in ["Work", "Personal", "Both"]:
        tile = page.locator("#scopes .tile", has_text=label)
        assert tile.locator(".tile__count").count() == 0
        assert tile.locator(".tile__name").count() == 0


def test_zero_due_tile_is_victorious(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("index.html", csv_path, date="2025-01-01"))

    all_tile = page.locator("#scopes .tile", has_text="All")
    assert "Victorious" in all_tile.inner_text()
    assert all_tile.locator(".tile__name").count() == 0


def test_loading_shows_four_skeletons(page, page_url, csv_copy, hold_route):
    csv_path = csv_copy("test_contexts.csv")
    release = hold_route(page, "**/context/*")
    try:
        page.goto(
            page_url("index.html", csv_path, date="2026-05-01"), wait_until="domcontentloaded"
        )
        page.wait_for_selector(".skeleton-tile")
        assert page.locator(".skeleton-tile").count() == 4
    finally:
        release()


def test_error_hides_tiles_and_shows_retry(page, page_url, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    page.route("**/context/*", lambda route: route.abort())
    try:
        page.goto(page_url("index.html", csv_path, date="2026-05-01"), wait_until="networkidle")
        assert page.locator("#error").is_visible()
        assert "Couldn't load" in page.inner_text("#error")
        assert page.locator("#scopes").is_hidden()
        assert page.locator("[data-retry]").is_visible()
    finally:
        page.unroute("**/context/*")


def _assert_oval_label(item, label):
    text = item.inner_text()
    assert text == label or text.endswith(" " + label)


def _assert_current(item, label):
    _assert_oval_label(item, label)
    assert item.get_attribute("aria-current") == "page"
    assert item.evaluate("el => el.tagName") == "SPAN"
    assert "breadcrumb__item--current" in (item.get_attribute("class") or "").split()


def _assert_link(item, label):
    _assert_oval_label(item, label)
    assert item.evaluate("el => el.tagName") == "A"
    assert "breadcrumb__item--current" not in (item.get_attribute("class") or "").split()


def _assert_oval_height(item):
    oval = item.locator(".breadcrumb__oval")
    assert oval.count() == 1
    box = oval.bounding_box()
    assert box is not None
    assert abs(box["height"] - 32) <= 1
    return oval


def _assert_current_absorbs(items):
    current = items.nth(items.count() - 1)
    current_box = current.locator(".breadcrumb__oval").bounding_box()
    assert current_box is not None
    for index in range(items.count() - 1):
        ancestor_box = items.nth(index).locator(".breadcrumb__oval").bounding_box()
        assert ancestor_box is not None
        assert current_box["width"] > ancestor_box["width"]


def _assert_trail(items):
    for index in range(items.count()):
        _assert_oval_height(items.nth(index))
    nav = items.first.locator("xpath=..")
    assert nav.evaluate("el => getComputedStyle(el).display") == "flex"
    if items.count() > 1:
        for index in range(items.count() - 1):
            assert items.nth(index).evaluate("el => getComputedStyle(el).flexGrow") == "0"
        assert items.nth(items.count() - 1).evaluate("el => getComputedStyle(el).flexGrow") == "1"
        _assert_current_absorbs(items)


def _assert_targets(item):
    box = item.bounding_box()
    assert box is not None
    assert box["height"] >= 44
    assert box["width"] >= 44


def _assert_fits(item):
    oval = _assert_oval_height(item)
    assert oval.evaluate("el => el.scrollWidth <= el.clientWidth + 1")


def _assert_search_stub(header):
    button = header.locator(".search-button")
    assert button.count() == 1
    assert button.get_attribute("aria-label") == "Search"
    assert button.get_attribute("aria-disabled") == "true"
    assert button.get_attribute("href") is None
    assert button.evaluate("el => el.tagName") == "BUTTON"
    box = button.bounding_box()
    assert box is not None
    assert box["width"] >= 44
    assert box["height"] >= 44
    nav_box = header.locator(".breadcrumb").bounding_box()
    assert nav_box is not None
    assert box["x"] >= nav_box["x"] + nav_box["width"] - 1


def test_breadcrumb_trail_is_consistent_across_pages(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")

    open_page(page, page_url("index.html", csv_path, date="2026-05-01"))
    header = page.locator("#pageHeader")
    assert header.locator(".breadcrumb").count() == 1
    assert header.locator(".page-title").count() == 0
    assert header.locator(".subtitle").count() == 0
    home_items = header.locator(".breadcrumb__item")
    assert home_items.count() == 1
    _assert_current(home_items.nth(0), "Recurrator")
    _assert_trail(home_items)
    _assert_search_stub(header)
    home_width = home_items.nth(0).bounding_box()["width"]
    nav_width = header.locator(".breadcrumb").bounding_box()["width"]
    assert abs(home_width - nav_width) < 1

    open_page(page, page_url("scope.html", csv_path, scope="work", date="2026-05-01"))
    header = page.locator("#pageHeader")
    assert header.locator(".page-title").count() == 0
    assert header.locator(".subtitle").count() == 0
    assert page.locator(".home-button").count() == 0
    scope_items = header.locator(".breadcrumb__item")
    assert scope_items.count() == 2
    _assert_link(scope_items.nth(0), "Recurrator")
    _assert_current(scope_items.nth(1), "Work")
    _assert_trail(scope_items)
    _assert_search_stub(header)
    _assert_targets(scope_items.nth(0))
    assert page.locator(".context-card").count() == 3

    open_page(page, page_url("context.html", csv_path, context="chores", date="2026-05-01"))
    header = page.locator("#pageHeader")
    assert header.locator(".page-title").count() == 0
    assert header.locator(".subtitle").count() == 0
    context_items = header.locator(".breadcrumb__item")
    assert context_items.count() == 3
    _assert_link(context_items.nth(0), "Recurrator")
    _assert_link(context_items.nth(1), "All")
    _assert_current(context_items.nth(2), "chores")
    _assert_trail(context_items)
    _assert_search_stub(header)
    _assert_targets(context_items.nth(0))
    _assert_targets(context_items.nth(1))
    assert page.locator(".task-row").count() == 3

    open_page(
        page,
        page_url("context.html", csv_path, context="chores", scope="personal", date="2026-05-01"),
    )
    header = page.locator("#pageHeader")
    personal_items = header.locator(".breadcrumb__item")
    assert personal_items.count() == 3
    _assert_link(personal_items.nth(1), "Personal")
    _assert_fits(personal_items.nth(1))
    _assert_trail(personal_items)

    open_page(page, page_url("task.html", csv_path, id=1, date="2026-05-01"))
    assert page.locator("#pageHeader .breadcrumb").count() == 1
    assert page.locator(".monster-card .breadcrumb").count() == 0
    card_items = page.locator("#pageHeader .breadcrumb__item")
    assert card_items.count() == 4
    _assert_link(card_items.nth(0), "Recurrator")
    _assert_link(card_items.nth(1), "All")
    _assert_link(card_items.nth(2), "casa")
    _assert_current(card_items.nth(3), "#1")
    _assert_trail(card_items)
    assert header.locator(".search-button").count() == 0
    assert (
        card_items.nth(3)
        .locator(".breadcrumb__oval")
        .evaluate("el => getComputedStyle(el).fontSize")
        == "11px"
    )
    _assert_targets(card_items.nth(0))
    _assert_targets(card_items.nth(1))
    _assert_targets(card_items.nth(2))
    assert page.locator(".monster-card__title").inner_text() == "Reparar fuga escusado"
    badge = page.locator(".rating-badge")
    assert badge.count() == 1
    assert badge.locator(".rating-badge__value").inner_text() == "1500"
    assert badge.locator(".visually-hidden").text_content().strip() == "Rating"
    assert page.locator(".microtext").count() == 0

    rendered = page.evaluate("""() => ui.renderBreadcrumb([
            { label: 'Recurrator', href: '#' },
            { label: 'All', href: '#' },
            { label: 'casa', href: '#' },
            { label: '#999' },
        ])""")
    page.evaluate(
        """(html) => {
            const host = document.createElement('div');
            host.id = 'fakeHeader';
            host.style.width = '353px';
            host.innerHTML = html;
            document.querySelector('main').appendChild(host);
        }""",
        rendered,
    )
    fake_items = page.locator("#fakeHeader .breadcrumb__item")
    assert fake_items.count() == 4
    _assert_current(fake_items.nth(3), "#999")
    _assert_trail(fake_items)
    _assert_fits(fake_items.nth(3))
