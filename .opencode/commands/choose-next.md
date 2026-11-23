---
description: Compare promised API behavior with the implemented API, resolve conflicts, and rank the next items by dependencies, effort, and risk.
---

# Choose Next

Answer "what should I do next" for the public HTTP API under `/api`. Read the promises, measure the current state, reconcile contradictions, and rank the work. The terminal carries the answer; `./next-backlog-items.html` carries the evidence.

## Preconditions

- Work from the repository root.
- `DOCS.md`, `TODO.md`, and `specs/` must be clean: `git status --porcelain -- <path>` prints nothing. If not, name the dirty path and stop.
- `next-backlog-items.html` must be ignored: `git check-ignore -q next-backlog-items.html`. If not, report the missing rule and stop.
- `docker ps --format '{{.Names}}'` must list `recurrator_dev`. If not, report and stop.
- `curl -fsS http://localhost/api/openapi.json` must return JSON with a non-empty `paths` object. If not, report and stop.
- `AGENTS.md` must define the public interface. If it does not, report and stop.

## Evidence

- OpenAPI is authoritative for routes, methods, and query parameters.
- Live probes are read-only and always pass `csv=/workdir/tests/data/<fixture>.csv`. Never call a write endpoint and never omit `csv`. A probe proves field presence and type, not behavior; a probe that contradicts OpenAPI is a finding, not a stop.
- Tests may be read and run; acceptance tests are preferred evidence. Never read production code: `recurrator/*.py` is out of bounds.
- `README.md` and `CHANGELOG.md` are not inputs.
- A TODO item belongs to the public interface only when it changes observable HTTP behavior or the published contract.

## Current state

Run `docker exec recurrator_dev make tests`, then `docker exec recurrator_dev make verify`. If either fails, report the failing nodes and stop; do not rank.

Classify every item:

- **verified**: a passing test or active criterion asserts it, or a probe matches the documented field shape. Behavior is verified only by tests.
- **present, unverified**: OpenAPI shows the route or parameter, or a probe shows the field, but no passing evidence covers it.
- **absent**: neither shows it.

## Items

The backlog is a flat list of items. Do not group items into packages or atoms.

- One criterion is one item.
- Otherwise, one uncovered observable behavior stated in `DOCS.md` or `TODO.md` is one item, quoted from its source. A TODO item that mirrors a criterion is the same item, and the item loses.
- An item names the surface it needs or introduces: a route, a response field, a query parameter, an error code, or a described behavior.
- A statement no acceptance test can express is not an item; it becomes a risk note on the item whose surface it touches.

## Dependencies

An edge runs from A to B when B's description or verify block names a surface that A introduces and the system does not serve. Quote that surface for every edge in the page.

- Apply the rule pair by pair, within a spec and across specs; same-spec order alone is not a dependency.
- The dependency count is the number of other items that cannot be implemented before the item, excluding itself.
- Implemented means the surface exists, not that a test passes. Counts fall as surfaces land.

## Conflicts and ambiguities

A conflict is two promises with incompatible behavior. An ambiguity is a statement with two or more readings where at least one collides with an unfulfilled promise. Unfulfilled means not yet true in the repository, not merely untested; discard a reading pinned by an active criterion or the implementation.

Interview one item at a time. Show both sides and offer options, each with its exact edit: one option per side or reading, always remove the other promise, and free-form. Wait for the answer; never resolve anything yourself.

Collect every choice, then apply them once:

- May write `DOCS.md`, `TODO.md`, and a skipped criterion whose test does not exist.
- Never write an active criterion, a test, `README.md`, `CHANGELOG.md`, or `AGENTS.md`.
- Refuse to delete the last promise for an implemented public element.
- Re-derive the promise set and re-check conflicts; a new conflict joins the session, and a repeating one stops the run.
- Never stage or commit.

An interrupted interview writes nothing.

## Dedupe

Before ranking, delete a public TODO item that mirrors a criterion when the criterion carries every value and relation it states. Keep implementation detail that survives; never rewrite the criterion.

## Readiness

- An item is ready when every surface it depends on already exists.
- Blocked items are listed with their blockers and never ranked.

## Effort

- Count the absent surfaces the item introduces: zero when its behavior exists, and one per new route, response field, query parameter, or error code.
- Add one when the item needs a runtime dependency the project does not have.
- Measure what the item introduces, not what it consumes.

## Risk

Assign risk flags per item, from what it introduces, and quote the evidence in the page: mutates task data; adds a runtime dependency; changes a documented response shape or status; states behavior no acceptance test can express.

## Ranking

Rank ready items only, in this order:

1. dependency count, descending
2. effort, ascending
3. risk flags, ascending
4. spec path, then criterion order

The table has no readiness column. The recommendation is the top item, with its spec path, test node, and action: `atdd-red` for a criterion item, and add its criterion and test first for an orphan. Never create the criterion.

## Verify and report

After applying, run `docker exec recurrator_dev make verify`. If it fails, report and leave the edits for inspection; do not repair.

Overwrite `./next-backlog-items.html` with a self-contained page; no external assets, no history. It holds four sections:

1. **Recommended**: the item, its action, and one line of rationale.
2. **Ranked**: rank, item, dependencies, effort, risk, and the quoted surface for each edge below the table.
3. **Blocked**: each blocked item and its blockers.
4. **Applied**: each resolution and dedupe edit, file and old to new.

It also states the verified, ready, and blocked totals. Print the recommendation, the top ten ready rows, the totals, and the page path. If nothing is missing and nothing is conflicting, say so and record the counts.

## Idempotency

The durable actions are the resolution edits, the dedupe deletions, and the page overwrite; each requires that the conflict or duplicate exists, and after it does not. The fixed rules make the same commit produce the same ranking. A second run finds no conflict, deletes nothing, rewrites the same page, and reports the same ranking. The page is rewritten every run by design, including a run with nothing to do.
