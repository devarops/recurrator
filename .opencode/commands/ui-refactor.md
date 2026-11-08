---
description: Apply one small, safe, behaviour-preserving refactoring to the frontend.
---

We are now in the Refactor phase of the frontend TDD loop.

Refactor improves the internal structure of the frontend and its browser tests without changing
observable behaviour. Apply exactly one refactoring per invocation.

## Task

- Work from the repository root. Verify the working tree is clean; if not, list it and stop.
- Read the full text of recent commit messages for the lessons, rationale, and recommendations.
- Run `docker exec recurrator_dev make test-frontend`; every test must pass. If any fails,
  report it and stop.
- Identify safe, behaviour-preserving refactoring opportunities in `public/`, excluding
  `public/styleguide.html`, and in `tests/browser/`.
- Use the catalog at https://refactoring.com/catalog/ and the style guide at
  https://islas.dev/guia_de_estilo/STYLEGUIDE.
- Prioritize readability, naming, duplication, dead code, and clarity over line count.
- Apply only the single most important refactoring. If no safe refactoring remains, report that
  and stop without writing or committing.
- Never touch `tests/visual/capture.py`, fixtures, the spec, the styleguide, or `approved/`.
- Never touch `recurrator/`, `api.py`, `DOCS.md`, `CHANGELOG.md`, `specs/`, or
  `tests/test_api.py`.
- Run `docker exec recurrator_dev make test-frontend` after the refactoring. If any test fails,
  run `git restore .` and report it. Do not try to repair the failed refactoring.
- Commit the refactoring with the message below.
- Report the commit hash and `git revert <hash>`. Stop.
- A second run applies the next safe refactoring. When none remains, it reports that and stops
  without writing.

## Format

- First line: `♻️🧪 <name from the refactoring catalog>`
- Second line: blank.
- Body paragraphs:
  1. The rationale and how the refactoring improves the code.
  2. How behaviour is preserved.
  3. Trade-offs, risks, or limitations.
- Do not use Conventional Commit prefixes. Do not amend, push, or stage unrelated files.
