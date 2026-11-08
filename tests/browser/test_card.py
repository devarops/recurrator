import csv
from datetime import date


def test_due_starred_card(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("task.html", csv_path, id=1, date="2026-05-01"))

    card = page.locator(".monster-card")
    assert "monster-card--due" in card.get_attribute("class")
    assert page.locator(".monster-card__title").inner_text() == "Reparar fuga escusado"
    assert page.locator(".monster-card__subtitle").inner_text() == "casa · every 21 days"
    assert page.locator(".bounty-badge").get_attribute("aria-label") == "Starred"
    assert page.locator(".bounty-badge--star").count() == 1
    assert page.locator(".bounty-badge__value").inner_text() == "42"
    assert page.locator(".status-line").inner_text() == "Overdue by 6 days"
    assert page.locator(".stat__value").all_inner_texts() == [
        "21 days",
        "0",
        "2026-04-25",
        "2026-04-04",
    ]
    assert page.locator("#doneBtn").is_enabled()
    assert page.locator("#doneLabel").get_attribute("aria-live") == "polite"
    assert page.locator(".btn--secondary").get_attribute("aria-disabled") == "true"


def test_not_due_unstarred_card(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    open_page(page, page_url("task.html", csv_path, id=10, date="2026-05-01"))

    card = page.locator(".monster-card")
    assert "monster-card--not-due" in card.get_attribute("class")
    assert page.locator(".bounty-badge").get_attribute("aria-label") == "Not starred"
    assert page.locator(".bounty-badge--circle").count() == 1
    assert page.locator(".status-line").inner_text() == "Due in 28 days"


def test_done_flow_updates_the_card_and_fixture(page, page_url, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    page.goto(page_url("task.html", csv_path, id=1), wait_until="networkidle")
    page.evaluate("document.fonts.ready.then(() => true)")

    assert page.locator("#doneBtn").is_enabled()
    page.locator("#doneBtn").click()
    page.wait_for_function(
        "document.getElementById('doneLabel').textContent.includes('Done today')"
    )

    assert page.locator("#doneLabel").inner_text() == "Done today ✓"
    assert page.locator("#doneBtn").is_disabled()

    with open(csv_path, newline="") as handle:
        rows = list(csv.DictReader(handle))
    row = next(item for item in rows if item["id"] == "1")
    assert row["date_4"] == date.today().isoformat()


def test_done_failure_restores_the_button(page, page_url, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    page.goto(page_url("task.html", csv_path, id=1), wait_until="networkidle")
    page.evaluate("document.fonts.ready.then(() => true)")

    page.route("**/task/*/done*", lambda route: route.abort())
    try:
        page.locator("#doneBtn").click()
        page.wait_for_selector("#saveError:not([hidden])")
        assert page.locator("#doneLabel").inner_text() == "✓ Mark as Done"
        assert page.locator("#doneBtn").is_enabled()
    finally:
        page.unroute("**/task/*/done*")


def test_card_loading_shows_skeleton(page, page_url, csv_copy, hold_route):
    csv_path = csv_copy("test_contexts.csv")
    release = hold_route(page, "**/task/*")
    try:
        page.goto(
            page_url("task.html", csv_path, id=1, date="2026-05-01"),
            wait_until="domcontentloaded",
        )
        page.wait_for_selector(".skeleton-monster")
        assert page.locator(".skeleton-monster").is_visible()
    finally:
        release()


def test_card_error_shows_retry(page, page_url, csv_copy):
    csv_path = csv_copy("test_contexts.csv")
    page.route("**/task/*", lambda route: route.abort())
    try:
        page.goto(
            page_url("task.html", csv_path, id=1, date="2026-05-01"),
            wait_until="networkidle",
        )
        assert page.locator("#error").is_visible()
        assert "Couldn't load" in page.inner_text("#error")
        assert page.locator("#task").is_hidden()
    finally:
        page.unroute("**/task/*")


def test_markdown_checklist_on_the_card(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_markdown.csv")
    open_page(page, page_url("task.html", csv_path, id=3, date="2026-05-01"))

    assert page.locator(".description .check-item").count() == 4
    assert page.locator(".description input[type=checkbox]").count() == 4
    assert page.locator(".description input[type=checkbox]").first.is_checked() is False


def test_checklist_rows_are_visually_compact(page, page_url, open_page, csv_copy):
    csv_path = csv_copy("test_markdown.csv")
    open_page(page, page_url("task.html", csv_path, id=3, date="2026-05-01"))

    labels = page.locator(".description .check-item label")
    first = labels.nth(0).bounding_box()
    second = labels.nth(1).bounding_box()

    assert first["height"] >= 44
    assert second["y"] - first["y"] < 30
