---
description: Compare received visual approval screenshots with approved baselines and the frontend reference, then approve or request another iteration.
---

# Approval Testing

You are the semantic comparator of a frontend approval test. You never approve on your own: the
human is the approver. The human runs `docker exec recurrator_dev make visual` before this
command; do not run it.

## Preconditions

- Work from the repository root (`git rev-parse --show-toplevel`).
- `tests/visual/received/` must contain at least one `*.png`. If it is missing or empty, report
  `No received screenshots. Run docker exec recurrator_dev make visual first.` and stop.
- `tests/visual/specs/recurrator-frontend-spec.md` must exist. If it does not, report and stop.
- `git status --porcelain` must be empty apart from ignored files. If it is not, list the changes
  and stop: the approval commit must contain only the approval.
- Read `tests/visual/specs/recurrator-frontend-spec.md` once. Read a mockup only as illustration.

## Scenarios

- Every `tests/visual/received/<screen>--<state>.png` is one scenario.
- `<screen>` is one of `home`, `scope`, `context`, `card`. Group by screen.
- The approved counterpart is `tests/visual/approved/<same file name>.png`. It may be absent; that
  is a first run.
- Ignore every other file.

## Comparison

For each scenario:

1. If the approved file exists and their `sha256sum` values match, mark it `same`; no visual
   judgement is needed.
2. Otherwise read the received image and, when present, the approved image. Judge whether they are
   semantically the same.
   - Any visible difference is meaningful, except the known-acceptable differences: emoji glyph
     family (Noto on Linux, Apple in the mockups), font rasterization and anti-aliasing, and
     scrollbar rendering.
   - A difference in text, geometry, colour, spacing, radius, shadow, weight, or clipping is
     meaningful, even when a changed fixture caused it.
3. If the scenario is `same`, or there is no approved file, compare it with the reference:
   - The spec is authoritative. Where the spec gives an explicit value it overrides the mockup, for
     example the primary button is 48px, micro-labels are 11px, and tap targets are at least 44px.
   - The mockup illustrates only what the spec leaves open. A screen's mockup is
     `tests/visual/specs/<screen>.png`.
   - Agreement is `done`. A deviation is `iterate`, and you name the rule and the rendered state it
     contradicts.
4. `approve` means a meaningful difference from the approved baseline. `iterate` means a deviation
   from the reference. `done` needs both to agree.

## Report

- Group by screen. Give each screen one verdict: `done` when every state is done; otherwise
  `approve` or `iterate`, with every state that needs action expanded under it, its difference
  named, and the paths of both images so the human can open them.
- Do not print states that are done beyond the screen verdict.
- End with counts per action and the capture time (mtime of the newest received file), so a stale
  capture is visible.
- Then ask the human which screens to approve, which to iterate, or reject. Wait for the answer.

## Approval

Act only after the human explicitly approves in this session.

- Accept `approve all`, `approve home and scope`, `approve none`, or `iterate`.
- For each approved scenario, copy `received/<name>.png` over `approved/<name>.png` and confirm the
  checksums match.
- If the human accepted a deviation from the reference, edit
  `tests/visual/specs/recurrator-frontend-spec.md` so it states the accepted behaviour in the same
  commit. Never edit a mockup PNG; if the mockup itself must change, say so and leave it to the
  human.
- Stage only `tests/visual/approved/` and the spec file.
- Commit with `📝 Approve visual baseline: <screens>` as the first line, a blank second line, and a
  body that lists the approved scenarios and any reference edits.
- Report the commit hash and the undo command, `git revert <hash>`.
- If every approved scenario is already identical and no reference edit is needed, report
  `Nothing to approve.` and stop without committing.

## Rejection and iteration

- Copy nothing and commit nothing.
- List the scenarios to fix and the rule or accepted change for each.
- Stop.

## Rules

- Never modify `approved/` or commit without an explicit approval in this session.
- Never stage `tests/visual/received/`.
- Never run `make visual`, `git push`, or touch production data.
- Never invent a scenario that is not in `received/`.
