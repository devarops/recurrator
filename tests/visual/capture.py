#!/usr/bin/env python3
"""Capture the approval-testing screenshots into tests/visual/received.

Run inside the development container with `docker exec recurrator_dev make
visual`. The script starts its own API on an ephemeral port and copies the
fixture for every capture, because rendering a context writes skip data back to
the CSV.

Scenarios for screens that do not exist yet are skipped, so the matrix can grow
with the redesign. External requests are aborted: the spec forbids CDNs, and
localhost is a secure context where crypto.subtle would otherwise fetch a
Gravatar monster that production never loads.
"""

from __future__ import annotations

import argparse
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from playwright.sync_api import BrowserContext, Page, Route, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "public"
DATA = ROOT / "tests" / "data"
RECEIVED = ROOT / "tests" / "visual" / "received"

VIEWPORT_WIDTH = 393
VIEWPORT_HEIGHT = 873
# The spec's 1080x2400 art basis rounds to 1081x2401 at this scale factor.
DEVICE_SCALE_FACTOR = 2.75
STARTUP_TIMEOUT_SECONDS = 20.0
SETTLE_MILLISECONDS = 150
LOADING_MILLISECONDS = 500

API_PATH = re.compile(r"^/(?:context|task)(?:/|\?|$)")


@dataclass(frozen=True)
class Scenario:
    """One page, fixture, pinned date, and optional forced state."""

    screen: str
    state: str
    path: str
    fixture: str
    date: str
    force: str = ""
    requires: str = ""

    @property
    def name(self) -> str:
        return f"{self.screen}--{self.state}"


# The matrix follows the frontend spec, screens only. The no-due-date card is
# absent because _compute_dates asserts that the fourth date exists, so the
# frozen backend cannot serve that state. Home and scope skip themselves until
# the redesign creates the pages and their containers.
SCENARIOS = [
    Scenario(
        "home", "normal", "index.html", "test_contexts.csv", "2026-05-01", requires='id="scopes"'
    ),
    Scenario(
        "home", "zero-due", "index.html", "test_contexts.csv", "2025-01-01", requires='id="scopes"'
    ),
    Scenario(
        "home",
        "loading",
        "index.html",
        "test_contexts.csv",
        "2026-05-01",
        force="loading",
        requires='id="scopes"',
    ),
    Scenario(
        "home",
        "error",
        "index.html",
        "test_contexts.csv",
        "2026-05-01",
        force="error",
        requires='id="scopes"',
    ),
    Scenario(
        "scope",
        "normal",
        "scope.html?scope=all",
        "test_contexts.csv",
        "2026-05-01",
        requires='id="contexts"',
    ),
    Scenario(
        "scope",
        "empty",
        "scope.html?scope=all",
        "test_contexts.csv",
        "2025-01-01",
        requires='id="contexts"',
    ),
    Scenario(
        "scope",
        "loading",
        "scope.html?scope=all",
        "test_contexts.csv",
        "2026-05-01",
        force="loading",
        requires='id="contexts"',
    ),
    Scenario(
        "scope",
        "error",
        "scope.html?scope=all",
        "test_contexts.csv",
        "2026-05-01",
        force="error",
        requires='id="contexts"',
    ),
    Scenario(
        "context",
        "normal",
        "context.html?context=chores",
        "test_contexts.csv",
        "2026-05-01",
        requires='id="tasks"',
    ),
    Scenario(
        "context",
        "empty",
        "context.html?context=chores",
        "test_contexts.csv",
        "2025-01-01",
        requires='id="tasks"',
    ),
    Scenario(
        "context",
        "loading",
        "context.html?context=chores",
        "test_contexts.csv",
        "2026-05-01",
        force="loading",
        requires='id="tasks"',
    ),
    Scenario(
        "context",
        "error",
        "context.html?context=chores",
        "test_contexts.csv",
        "2026-05-01",
        force="error",
        requires='id="tasks"',
    ),
    Scenario("card", "due-starred", "task.html?id=1", "test_contexts.csv", "2026-05-01"),
    Scenario("card", "overdue-starred", "task.html?id=1", "test_contexts.csv", "2026-06-01"),
    Scenario("card", "not-due-unstarred", "task.html?id=10", "test_contexts.csv", "2026-05-01"),
]


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def start_api(port: int) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "recurrator.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wait_for_api(port: int) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    url = f"http://127.0.0.1:{port}/openapi.json"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.1)
    raise RuntimeError(f"the API did not start on port {port}")


def page_path(scenario: Scenario) -> Path:
    return PUBLIC / scenario.path.split("?", 1)[0]


def should_run(scenario: Scenario) -> bool:
    path = page_path(scenario)
    if not path.is_file():
        print(f"skip {scenario.name}: {path.name} does not exist")
        return False
    if scenario.requires and scenario.requires not in path.read_text(encoding="utf-8"):
        print(f"skip {scenario.name}: {path.name} lacks {scenario.requires}")
        return False
    return True


def route_request(route: Route, base_url: str, force: str, pending: list[Route]) -> None:
    request_url = route.request.url
    if API_PATH.match(urlsplit(request_url).path):
        if force == "error":
            route.abort()
            return
        if force == "loading":
            pending.append(route)
            return
    if request_url.startswith(base_url):
        route.continue_()
        return
    route.abort()


def capture(page: Page, scenario: Scenario, port: int) -> bytes:
    base_url = f"http://127.0.0.1:{port}/"
    tempdir = Path(tempfile.mkdtemp(prefix="recurrator-visual-"))
    try:
        csv_path = tempdir / scenario.fixture
        shutil.copyfile(DATA / scenario.fixture, csv_path)

        query = urlencode({"csv": str(csv_path), "date": scenario.date})
        separator = "&" if "?" in scenario.path else "?"
        url = f"{base_url}{scenario.path}{separator}{query}"

        pending: list[Route] = []
        page.route("**/*", lambda route: route_request(route, base_url, scenario.force, pending))
        try:
            page.goto(url, wait_until="domcontentloaded")
            page.evaluate("document.fonts.ready.then(() => true)")
            if scenario.force == "loading":
                page.wait_for_timeout(LOADING_MILLISECONDS)
            else:
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(SETTLE_MILLISECONDS)
            page.evaluate("window.scrollTo(0, 0)")
            return page.screenshot(full_page=False, animations="disabled", caret="hide")
        finally:
            for route in pending:
                route.abort()
            page.unroute("**/*")
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)


def single_capture(context: BrowserContext, scenario: Scenario, port: int) -> bytes:
    page = context.new_page()
    try:
        return capture(page, scenario, port)
    finally:
        page.close()


def check_stability(context: BrowserContext, scenarios: list[Scenario], port: int) -> int:
    failures = 0
    for scenario in scenarios:
        first = single_capture(context, scenario, port)
        second = single_capture(context, scenario, port)
        if first == second:
            print(f"stable {scenario.name}")
        else:
            failures += 1
            print(f"unstable {scenario.name}")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="capture twice and compare without writing"
    )
    args = parser.parse_args()

    scenarios = [scenario for scenario in SCENARIOS if should_run(scenario)]
    if not scenarios:
        print("no scenarios to capture")
        return 1

    if not args.check:
        RECEIVED.mkdir(parents=True, exist_ok=True)
        for stale in RECEIVED.glob("*.png"):
            stale.unlink()

    port = free_port()
    api = start_api(port)
    try:
        wait_for_api(port)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = browser.new_context(
                viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
                device_scale_factor=DEVICE_SCALE_FACTOR,
                timezone_id="America/Los_Angeles",
                locale="en-US",
                color_scheme="light",
                reduced_motion="reduce",
            )
            try:
                if args.check:
                    return check_stability(context, scenarios, port)
                for scenario in scenarios:
                    data = single_capture(context, scenario, port)
                    (RECEIVED / f"{scenario.name}.png").write_bytes(data)
                    print(f"captured {scenario.name}")
                return 0
            finally:
                context.close()
                browser.close()
    finally:
        api.terminate()
        try:
            api.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api.kill()


if __name__ == "__main__":
    sys.exit(main())
