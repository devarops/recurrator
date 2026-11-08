#!/usr/bin/env python3
"""Render the before/after approval review page from a comparison report.

The report is JSON with capture_time, head, suites, and one entry per changed
or new scenario. Approved and received images are paired by file name; the
helper computes same/changed/new from hashes, refuses a report that omits a
changed or new scenario, and writes tests/visual/review.html.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VISUAL = ROOT / "tests" / "visual"
RECEIVED = VISUAL / "received"
APPROVED = VISUAL / "approved"
OUTPUT = VISUAL / "review.html"
SCREEN_ORDER = ("home", "scope", "context", "card")

CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #f5f2ea;
  color: #2f2a26;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
main { max-width: 980px; margin: 0 auto; padding: 24px 20px 48px; }
h1 { font-size: 24px; margin: 0 0 8px; }
h2 {
  font-size: 16px;
  text-transform: uppercase;
  letter-spacing: .06em;
  margin: 32px 0 12px;
  color: #6b5f55;
}
h3 { font-size: 16px; margin: 0; }
.meta, .counts { margin: 4px 0; font-size: 13px; color: #6b5f55; }
.counts { font-weight: 600; color: #2f2a26; }
.card {
  background: #fffdf8;
  border: 1px solid #d8cec2;
  border-radius: 10px;
  padding: 16px;
  margin: 0 0 18px;
}
.card__head {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: baseline;
  justify-content: space-between;
}
.state { font-weight: 400; color: #6b5f55; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .04em;
  text-transform: uppercase;
  background: #ece5da;
  color: #4a4038;
}
.chip--changed, .chip--new { background: #f6d9b8; color: #6b3200; }
.chip--spec-match { background: #d9e8d0; color: #2f4f1f; }
.chip--spec-gap { background: #f3e3a6; color: #5a4500; }
.chip--spec-contradiction { background: #f3c4bd; color: #7a1300; }
.chip--unexpected { background: #e4c7f0; color: #4d175e; }
.chip--expected { background: #d9e8d0; color: #2f4f1f; }
.note { margin: 12px 0 16px; white-space: pre-wrap; font-size: 14px; line-height: 1.45; }
.pair { display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-start; }
figure { margin: 0; flex: 1 1 320px; max-width: 460px; }
figcaption {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: #6b5f55;
  margin-bottom: 6px;
}
figure img {
  display: block;
  width: 100%;
  height: auto;
  border: 1px solid #d8cec2;
  border-radius: 6px;
  background: #fff;
}
.missing {
  display: grid;
  place-items: center;
  min-height: 240px;
  border: 1px dashed #b9a99a;
  border-radius: 6px;
  color: #6b5f55;
  font-size: 13px;
}
.banner { padding: 16px; border-radius: 10px; background: #d9e8d0; color: #2f4f1f; font-weight: 600; }
.warning {
  margin: 24px 0;
  padding: 12px 16px;
  border-radius: 10px;
  background: #f3e3a6;
  color: #5a4500;
}
.warning h2 { margin-top: 0; color: inherit; }
.unchanged { margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6; }
@media (max-width: 640px) {
  .pair { display: block; }
  figure { max-width: none; margin-bottom: 16px; }
}
"""


def parse_args() -> Path:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="JSON comparison report from ui-approve")
    return parser.parse_args().report


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_name(name: str) -> tuple[str, str]:
    screen, _, state = name.partition("--")
    return screen, state or name


def pair_status(received: Path) -> str:
    approved = APPROVED / received.name
    if not approved.is_file():
        return "new"
    return "same" if digest(approved) == digest(received) else "changed"


def load_report(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        report = json.load(handle)
    if not isinstance(report, dict) or not isinstance(report.get("scenarios"), list):
        raise ValueError("report must contain a scenarios list")
    return report


def validate(
    report: dict[str, Any],
    received_names: set[str],
    statuses: dict[str, str],
) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for raw in report["scenarios"]:
        if not isinstance(raw, dict):
            raise ValueError("every scenario entry must be an object")
        name = str(raw.get("name", ""))
        if not name:
            raise ValueError("every scenario entry needs a name")
        if name not in received_names:
            raise ValueError(f"report names a scenario that was not captured: {name}")
        if statuses[name] == "same":
            continue
        spec = raw.get("spec")
        if spec not in {"match", "gap", "contradiction"}:
            raise ValueError(f"{name}: spec must be match, gap, or contradiction")
        scope = raw.get("scope")
        if scope not in {"expected", "unexpected"}:
            raise ValueError(f"{name}: scope must be expected or unexpected")
        note = raw.get("note")
        if not isinstance(note, str) or not note.strip():
            raise ValueError(f"{name}: a note is required")
        entries[name] = raw
    missing = sorted(
        name for name, value in statuses.items() if value != "same" and name not in entries
    )
    if missing:
        raise ValueError("report omits changed or new scenarios: " + ", ".join(missing))
    return entries


def group_by_screen(names: list[str]) -> list[tuple[str, list[str]]]:
    groups: dict[str, list[str]] = {}
    for name in names:
        screen, _ = split_name(name)
        groups.setdefault(screen, []).append(name)
    return sorted(
        groups.items(),
        key=lambda item: (
            SCREEN_ORDER.index(item[0]) if item[0] in SCREEN_ORDER else len(SCREEN_ORDER),
            item[0],
        ),
    )


def chip(text: str, kind: str) -> str:
    return f'<span class="chip chip--{kind}">{html.escape(text)}</span>'


def figure(label: str, path: Path, name: str) -> str:
    relative = path.relative_to(VISUAL).as_posix()
    return (
        "<figure>"
        f"<figcaption>{html.escape(label)}</figcaption>"
        f'<a href="{relative}"><img src="{relative}" alt="{html.escape(name)}"></a>'
        "</figure>"
    )


def missing_figure(label: str) -> str:
    return (
        "<figure>"
        f"<figcaption>{html.escape(label)}</figcaption>"
        '<div class="missing">No approved baseline</div>'
        "</figure>"
    )


def card(name: str, status: str, entry: dict[str, Any]) -> str:
    screen, state = split_name(name)
    approved = APPROVED / f"{name}.png"
    received = RECEIVED / f"{name}.png"
    chips = chip(status, status)
    chips += chip(f"spec {entry['spec']}", f"spec-{entry['spec']}")
    chips += chip(str(entry["scope"]), str(entry["scope"]))
    before = (
        figure("Approved (before)", approved, name)
        if approved.is_file()
        else missing_figure("Approved (before)")
    )
    after = figure("Received (after)", received, name)
    return (
        '<article class="card">'
        '<header class="card__head">'
        f'<h3>{html.escape(screen)} <span class="state">{html.escape(state)}</span></h3>'
        f'<div class="chips">{chips}</div>'
        "</header>"
        f'<p class="note">{html.escape(str(entry["note"]))}</p>'
        f'<div class="pair">{before}{after}</div>'
        "</article>"
    )


def unchanged(names: list[str]) -> str:
    if not names:
        return '<p class="unchanged">None.</p>'
    items = []
    for screen, group in group_by_screen(names):
        states = ", ".join(split_name(name)[1] for name in group)
        items.append(f"<li><strong>{html.escape(screen)}</strong>: {html.escape(states)}</li>")
    return '<ul class="unchanged">' + "".join(items) + "</ul>"


def orphans(received_names: set[str]) -> list[str]:
    return sorted(path.stem for path in APPROVED.glob("*.png") if path.stem not in received_names)


def render(
    report: dict[str, Any],
    statuses: dict[str, str],
    entries: dict[str, dict[str, Any]],
) -> str:
    changed = sorted(name for name, value in statuses.items() if value != "same")
    same = sorted(name for name, value in statuses.items() if value == "same")
    capture_time = html.escape(str(report.get("capture_time", "unknown")))
    head = html.escape(str(report.get("head", "unknown")))
    suites = report.get("suites")
    suite_line = ""
    if isinstance(suites, dict):
        suite_line = " · ".join(
            f"{html.escape(str(key))}: {html.escape(str(value))}" for key, value in suites.items()
        )
    suite_html = f'<p class="meta">{suite_line}</p>' if suite_line else ""

    if changed:
        sections = []
        for screen, group in group_by_screen(changed):
            cards = "".join(card(name, statuses[name], entries[name]) for name in group)
            sections.append(f"<section><h2>{html.escape(screen)}</h2>{cards}</section>")
        changed_html = "".join(sections)
    else:
        changed_html = '<p class="banner">No visual difference. Nothing to approve.</p>'

    orphan_names = orphans(set(statuses))
    if orphan_names:
        items = "".join(f"<li>{html.escape(name)}</li>" for name in orphan_names)
        warning_html = (
            '<section class="warning"><h2>Approved but not captured</h2>'
            f"<ul>{items}</ul></section>"
        )
    else:
        warning_html = ""

    same_html = f"<section><h2>Unchanged</h2>{unchanged(same)}</section>" if same else ""
    counts = f"{len(changed)} changed or new · {len(same)} unchanged"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Recurrator visual review</title>
<style>{CSS}</style>
</head>
<body>
<main>
<header>
<h1>Recurrator visual review</h1>
<p class="meta">Capture {capture_time} · HEAD {head}</p>
{suite_html}
<p class="counts">{counts}</p>
</header>
{changed_html}
{warning_html}
{same_html}
</main>
</body>
</html>
"""


def main() -> int:
    report_path = parse_args()
    try:
        report = load_report(report_path)
        received = {path.stem: path for path in RECEIVED.glob("*.png")}
        if not received:
            raise ValueError(f"no screenshots in {RECEIVED}")
        statuses = {name: pair_status(path) for name, path in received.items()}
        entries = validate(report, set(received), statuses)
        OUTPUT.write_text(render(report, statuses, entries), encoding="utf-8")
        print(OUTPUT)
        return 0
    except (OSError, ValueError) as error:
        print(f"review.py: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
