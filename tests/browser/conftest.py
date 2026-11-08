"""Fixtures for the Playwright frontend suite.

The suite runs inside the development image, which carries Playwright and
Chromium. The API starts on an ephemeral port, and each test receives a fresh
copy of a fixture CSV because rendering a context writes skip data.
"""

import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

import pytest
from playwright.sync_api import sync_playwright

if not os.environ.get("RUN_BROWSER"):
    collect_ignore_glob = ["test_*.py"]

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "tests" / "data"
VIEWPORT = {"width": 393, "height": 873}
STARTUP_TIMEOUT_SECONDS = 20.0
SETTLE_MILLISECONDS = 150


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _start_api(port):
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


def _wait_for_api(port):
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    url = f"http://127.0.0.1:{port}/openapi.json"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.1)
    raise RuntimeError("the API did not start")


@pytest.fixture(scope="session")
def api_base():
    port = _free_port()
    process = _start_api(port)
    try:
        _wait_for_api(port)
        yield f"http://127.0.0.1:{port}"
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            yield browser
        finally:
            browser.close()


@pytest.fixture(scope="session")
def context(browser):
    context = browser.new_context(
        viewport=VIEWPORT,
        device_scale_factor=1,
        timezone_id="America/Los_Angeles",
        locale="en-US",
        color_scheme="light",
        reduced_motion="reduce",
    )
    try:
        yield context
    finally:
        context.close()


@pytest.fixture
def page(context):
    page = context.new_page()
    try:
        yield page
    finally:
        page.close()


@pytest.fixture
def csv_copy(tmp_path):
    def copy(name):
        destination = tmp_path / name
        shutil.copyfile(DATA / name, destination)
        return str(destination)

    return copy


@pytest.fixture
def page_url(api_base):
    def build(page_name, csv_path, **params):
        query = {"csv": csv_path, **params}
        return f"{api_base}/{page_name}?{urlencode(query)}"

    return build


@pytest.fixture
def open_page():
    def open_(page, url):
        page.goto(url, wait_until="networkidle")
        page.evaluate("document.fonts.ready.then(() => true)")
        page.wait_for_timeout(SETTLE_MILLISECONDS)
        return page

    return open_


@pytest.fixture
def hold_route():
    def hold(page, pattern):
        pending = []

        def handler(route):
            pending.append(route)

        page.route(pattern, handler)

        def release():
            for route in pending:
                route.abort()
            page.unroute(pattern)

        return release

    return hold
