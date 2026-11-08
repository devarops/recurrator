def test_scope_lists_all_due_contexts(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("scope.html", csv_path, scope="all", date="2026-05-01"))

    assert page.locator(".context-card").count() == 3
    assert page.locator(".context-card__title").all_inner_texts() == ["casa", "chores", "laptop"]


def test_scope_empty_state(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("scope.html", csv_path, scope="all", date="2025-01-01"))

    assert page.locator(".empty__title").inner_text() == "You are victorious!"
    assert page.locator(".context-card").count() == 0


def test_scope_loading_shows_four_skeletons(page, page_url, csv_copy, hold_route):
    csv_path = csv_copy("test_contexts.csv")
    release = hold_route(page, "**/context/*")
    try:
        page.goto(
            page_url("scope.html", csv_path, scope="all", date="2026-05-01"),
            wait_until="domcontentloaded",
        )
        page.wait_for_selector(".skeleton-card")
        assert page.locator(".skeleton-card").count() == 4
    finally:
        release()


def test_scope_error_shows_retry(page, page_url, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    page.route("**/context/*", lambda route: route.abort())
    try:
        page.goto(
            page_url("scope.html", csv_path, scope="all", date="2026-05-01"),
            wait_until="networkidle",
        )
        assert page.locator("#error").is_visible()
        assert "Couldn't load" in page.inner_text("#error")
        assert page.locator("#contexts").is_hidden()
    finally:
        page.unroute("**/context/*")
