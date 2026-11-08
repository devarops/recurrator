---
description: Compare received captures with the approved baseline, publish a review page, and approve or reject the change.
---

You are the semantic comparator and approval recorder of the frontend approval test. The human
is the approver. You never approve on your own.

## Preconditions

- Work from the repository root (`git rev-parse --show-toplevel`).
- `git status --porcelain` must be empty. Ignored files do not appear; if tracked changes do,
  list them and stop: the approval commit must contain only the approval.
- `tests/visual/received/` must contain at least one `*.png`. If it is missing or empty, report
  `No received screenshots. Run docker exec recurrator_dev make visual first.` and stop.
- `tests/visual/specs/recurrator-frontend-spec.md` must exist. If it does not, report and stop.
- Enforce a fresh capture: compare the newest received mtime with the last commit touching
  `public/`, `tests/browser/`, or `tests/visual/capture.py`, using
  `git log -1 --format=%ct -- public tests/browser tests/visual/capture.py` and the newest
  `stat -c %Y` (or `find -printf '%T@'`) under `tests/visual/received/`. If the capture is older,
  report `Stale capture. Run docker exec recurrator_dev make visual again.` and stop.
- Run `docker exec recurrator_dev make test-frontend`, `docker exec recurrator_dev make tests`, and
  `docker exec recurrator_dev make verify`. Every suite must pass. If one fails, report it and stop;
  do not compare or approve. If the development container or qed is missing, report that and stop.
- Read `tests/visual/specs/recurrator-frontend-spec.md` once.
- Read `git log` since the last `📝 Approve visual baseline` commit, or the last eight commits if
  none. The bodies of the `🛑🧪` commits since the last approval name the expected screens and
  states; their union is the scope record.

## Scenarios

- Every `tests/visual/received/<screen>--<state>.png` is one scenario. Group by screen.
- The approved counterpart is `tests/visual/approved/<same file name>.png`. It may be absent; that
  is a new scenario.
- Ignore every other file.

## Comparison

For each scenario:

1. If the approved file exists and their `sha256sum` values match, mark it `same`; no visual
   judgement is needed.
2. Otherwise read the received image and, when present, the approved image. Any visible difference
   is meaningful: text, geometry, colour, spacing, radius, shadow, weight, or clipping, even when
   a fixture change caused it.
3. Mark `new` when there is no approved file; otherwise `changed`.
4. For every `changed` or `new` scenario:
   - Compare it with the reference. `spec match` when the spec already states it; `spec gap` when
     the spec is silent; `spec contradiction` when it breaks an explicit rule. Name the rule and
     the rendered state.
   - Compare it with the scope record. `expected` when the screen and state are inside it;
     `unexpected` otherwise.
   - Write one short note naming the visible difference and the rule or gap it relates to.

## Review page

- Write `/tmp/opencode/recurrator-review.json` with:
  - `capture_time`: mtime of the newest received file, ISO 8601.
  - `head`: `git rev-parse HEAD`.
  - `suites`: the three suite results.
  - `scenarios`: one entry for each `changed` or `new` scenario with `name`, `spec` (`match`,
    `gap`, or `contradiction`), `scope` (`expected` or `unexpected`), and `note`.
- Run `python tests/visual/review.py /tmp/opencode/recurrator-review.json`. It writes
  `tests/visual/review.html` and exits nonzero if the report omits a changed or new scenario.
- Print the absolute path of `review.html`, one line of counts per screen, and every `unexpected`
  or `spec contradiction`. Then ask the human to approve all or reject. Wait.

## Approval

Act only after the human explicitly decides in this session.

- Approval is all-or-nothing. Accept `approve all`, `approve all accepting <n> unexpected,
  <n> contradictions`, or `reject`. A partial screen request is not an approval; restate the rule
  and wait.
- If any scenario is `unexpected` or `spec contradiction`, require the explicit `accepting ...`
  form with the exact counts. A bare `approve all` is not enough.
- On rejection: copy nothing and commit nothing. List the rejected states, the rule or issue, and
  the received and approved paths. Stop.
- On approval:
  - Copy each `received/<name>.png` over `approved/<name>.png`, creating new files, and confirm
    the checksums match.
  - Edit the spec so every approved `spec gap` or `spec contradiction` states the accepted
    behaviour. Do not rewrite unrelated sections.
  - Update `public/styleguide.html` so every changed or new component or state has a matching
    sample. Do not change `ui.js`, CSS, or the app pages here.
  - Stage only `tests/visual/approved/`, the spec, and `public/styleguide.html`.
  - Commit with `📝 Approve visual baseline: <screens>` on the first line, a blank second line, and
    a body listing the approved scenarios, the reviewed HEAD, the spec edits, the styleguide
    edits, the acknowledged drift, and the fact that the browser tests, approved PNGs, spec, and
    styleguide now agree.
  - Report the commit hash and `git revert <hash>`.
- If every scenario is `same` and no document needs an edit, report
  `No visual difference; nothing to approve.` and stop. Do not invent a baseline.
- If every scenario is `same` but the spec or styleguide should record a behaviour-only change,
  report that and ask the human. On approval, edit only those documents and commit
  `📝 Record approved behaviour: <screens>`; copy no PNGs and print the undo command.

## Rules

- Never modify `approved/` or commit without an explicit approval in this session.
- Never stage `tests/visual/received/` or `tests/visual/review.html`.
- Never run `make visual`, `git push`, or touch production data.
- Never invent a scenario that is not in `received/`.
- Never touch `recurrator/`, `api.py`, `DOCS.md`, `CHANGELOG.md`, `specs/`, or
  `tests/test_api.py`.
- A second run after an approval finds `received/` equal to `approved/` and reports that there is
  nothing to approve; it does not commit again.
