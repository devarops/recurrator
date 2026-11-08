---
description: Write and validate the failing frontend test, or the visual scenario, for the requested change.
---

We are now in the Red phase of the frontend TDD loop.

The Red phase turns one requested frontend change into a failing frontend test, or, when the
change has no observable DOM behaviour, into a capture scenario whose diff is the pending
failure. It leaves production code untouched.

## Task

- Work from the repository root (`git rev-parse --show-toplevel`).
- Verify the working tree is clean: no staged, modified, deleted, or untracked files. If any
  uncommitted change exists, list it and stop.
- The invocation must name the change and the screens and states it is expected to touch. If it
  does not, report that and stop.
- Read `git log --patch --max-count 8` for the current position, lessons, and rationale.
- Read `tests/visual/specs/recurrator-frontend-spec.md`, `public/styleguide.html`, the existing
  `tests/browser/` tests, and the `SCENARIOS` in `tests/visual/capture.py`.
- Run `docker exec recurrator_dev make test-frontend`. If a browser test already fails, report it
  and stop: the red test is committed and the next step is `ui-green`.
- Decide whether the change has observable DOM behaviour:
  - If it does, write exactly one failing Playwright test for the requested behaviour. Put it in
    the matching `tests/browser/test_<screen>.py`; if no screen matches, use the closest existing
    file. Do not rewrite unrelated cases. When an existing assertion contradicts the requested
    change, update only that assertion. Keep exactly one test failing.
  - If it does not (a purely visual change such as colour, spacing, radius, or typography), do not
    write a Playwright test. The Red is a capture scenario that shows the change; the browser
    suite stays green and the visual diff becomes visible after `ui-green`.
- Add a capture scenario to `tests/visual/capture.py` only when no existing scenario can show the
  change. Use `<screen>--<state>`; the page must exist and satisfy `requires`, otherwise
  `should_run` skips it. Add a fixture under `tests/data/` only when needed, and only as a new
  file. Never modify a fixture that existing tests or scenarios use.
- Do not edit production code (`public/`), the spec, or the styleguide.
- Stage only `tests/browser/`, `tests/visual/capture.py`, a new fixture under `tests/data/`, and
  `tests/test_frontend.py` when the render contract changes. Never touch `recurrator/`, `api.py`,
  `DOCS.md`, `CHANGELOG.md`, `specs/`, or `tests/test_api.py`.
- Cover the requested change, not the whole redesign. Do not introduce premature generalization.
- A second run after the Red commit finds the committed failing test, reports that the next step
  is `ui-green`, and stops without writing.

## Validation

- Run `docker exec recurrator_dev make test-frontend`.
- For a behavioural Red, confirm that exactly one browser test fails and that the failure is an
  assertion or interface-absence error inside the test body, such as a missing element, wrong
  text, or wrong count. A collection, import, syntax, page-load, or timeout error caused by a
  broken test is not a valid Red.
- For a visual-only Red, confirm that the browser suite passes and that the new or updated
  scenario is present, its page exists, and its `requires` marker is present.
- If more than one test fails, or the failure is not the intended assertion, stop without
  committing.
- Stage only the test files, the scenario, a new fixture, and `tests/test_frontend.py` when the
  render contract changes. Commit with the message below.
- Report the commit hash and `git revert <hash>`. Stop. Do not proceed to Green.

## Format

- First line: `🛑🧪 <brief expected behaviour>`
- Second line: blank.
- Body paragraphs:
  1. The requested change and the screens and states it is expected to touch. This is the scope
     record `ui-approve` uses to flag drift.
  2. The test path and the assertion that fails, or, for a visual-only Red, the scenario and why
     the browser suite stays green.
  3. The spec rule or gap the change addresses.
  4. Confirmation that no other browser test fails.
- Do not use Conventional Commit prefixes. Do not amend, push, or stage unrelated files.
