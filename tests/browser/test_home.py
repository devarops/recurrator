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
