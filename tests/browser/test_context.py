def test_context_rows_are_sorted_by_coins(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("context.html", csv_path, context="chores", date="2026-05-01"))

    assert page.locator(".page-title").inner_text() == "chores"
    assert page.locator(".task-row").count() == 3
    assert page.locator(".task-row__title").all_inner_texts() == [
        "Recoger basura de",
        "Limpiar cuartito de",
        "Lavar uniformes taekwondo",
    ]
    assert page.locator(".bounty__value").all_inner_texts() == ["48", "35", "14"]


def test_context_empty_state(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("context.html", csv_path, context="chores", date="2025-01-01"))

    assert page.locator(".empty__title").inner_text() == "No monsters left here."
    assert page.locator(".empty__link").is_visible()


def test_context_loading_shows_six_skeletons(page, page_url, csv_copy, hold_route):
    csv_path = csv_copy("test_contexts.csv")
    release = hold_route(page, "**/context/*")
    try:
        page.goto(
            page_url("context.html", csv_path, context="chores", date="2026-05-01"),
            wait_until="domcontentloaded",
        )
        page.wait_for_selector(".skeleton-row")
        assert page.locator(".skeleton-row").count() == 6
    finally:
        release()


def test_context_error_shows_retry(page, page_url, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    page.route("**/context/*", lambda route: route.abort())
    try:
        page.goto(
            page_url("context.html", csv_path, context="chores", date="2026-05-01"),
            wait_until="networkidle",
        )
        assert page.locator("#error").is_visible()
        assert "Couldn't load" in page.inner_text("#error")
        assert page.locator("#tasks").is_hidden()
    finally:
        page.unroute("**/context/*")
