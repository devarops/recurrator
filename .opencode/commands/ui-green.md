---
description: Implement the frontend change that makes the failing test pass and the requested behaviour visible.
---

We are now in the Green phase of the frontend TDD loop.

Green turns the committed Red into working frontend code. The failing test is the behavioural
floor; the change described in the Red commit is the goal. Do not edit tests.

## Task

- Work from the repository root. Verify the working tree is clean; if not, list it and stop.
- Read the full text of the last few commit messages, especially the Red commit's scope record.
- Run `docker exec recurrator_dev make test-frontend`.
  - For a behavioural Red, confirm that exactly one test fails. If none fails, report that Green
    is already complete and stop. If more than one fails, report that and stop.
  - For a visual-only Red, the suite passes; the requirement is the scenario in the Red commit.
- Analyze the failing test, but infer the full requested change from the Red commit and the
  invocation. Implement the change, including the visual detail the test cannot assert. Do not
  reinterpret, weaken, or edit the test.
- Change only `public/`, excluding `public/styleguide.html`. Do not edit tests,
  `tests/visual/capture.py`, fixtures, the spec, the styleguide, or `approved/`.
- Never touch `recurrator/`, `api.py`, `DOCS.md`, `CHANGELOG.md`, `specs/`, or
  `tests/test_api.py`.
- Prefer the smallest change that makes the test pass and the described change visible.
  Generalize only when a previously passing test fails.
- Do not refactor, optimize, or improve structure beyond what the change needs.
- Run `docker exec recurrator_dev make test-frontend`; every test must pass.
- Commit only the production files with the message below.
- Report the commit hash and `git revert <hash>`. Stop. Do not proceed to Refactor.
- A second run after the Green commit finds the browser suite green and reports that Green is
  complete; it does not commit again.

## Format

- First line: `✅🧪 <brief imperative summary>`
- Second line: blank.
- Body paragraphs:
  1. How the change satisfies the failing test and the requested visual change.
  2. Why the implementation is minimal and does not generalize prematurely.
  3. Confirmation that the browser suite passes.
- Do not use Conventional Commit prefixes. Do not amend, push, or stage unrelated files.
