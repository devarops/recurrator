---
description: Compare promised API behavior with the implemented API, resolve conflicts, and rank the next backlog items.
---

# Choose Next

Answer "what should I do next" for the public HTTP API under `/api`. Read the promises, measure the current state, reconcile contradictions with the user, and rank the work. The terminal carries the answer; `./next-backlog-items.html` carries the evidence.

## Preconditions

- Work from the repository root (`git rev-parse --show-toplevel`).
- `DOCS.md`, `TODO.md`, and `specs/` must be clean: `git status --porcelain -- <path>` prints nothing for each. If not, name the dirty path and stop.
- `next-backlog-items.html` must be ignored: `git check-ignore -q next-backlog-items.html`. If not, report the missing ignore rule and stop.
- `docker ps --format '{{.Names}}'` must list `recurrator_dev`. If not, report and stop.
- `curl -fsS http://localhost/api/openapi.json` must return JSON with a non-empty `paths` object. If not, report and stop.
- Read `AGENTS.md` for the public-interface definition. If it is absent or lacks it, report and stop.

## Evidence

- OpenAPI is authoritative for routes, methods, and query parameters.
- Live probes are read-only and always pass `csv=/workdir/tests/data/<fixture>.csv`. Never call a write endpoint and never omit `csv`. A probe proves field presence and type, not behavior. A probe that contradicts OpenAPI is a finding, not a stop.
- Tests may be read and run; acceptance tests are preferred evidence. Never read production code: `recurrator/*.py` is out of bounds.
- `README.md` and `CHANGELOG.md` are not inputs.
- `AGENTS.md` defines the public interface as the HTTP API under `/api`. A TODO item belongs to it only when it changes observable HTTP behavior or the published contract. Ignore every other item.

## Current state

Run `docker exec recurrator_dev make tests`, then `docker exec recurrator_dev make verify`. If either fails, report the failing nodes and stop; do not rank.

Classify every atom:

- **verified** — a passing test or active criterion asserts it, or a probe matches the documented field shape. Behavior is verified only by tests.
- **present, unverified** — OpenAPI shows the route or parameter, or a probe shows the field, but no passing evidence covers it.
- **absent** — neither shows it.

## Atoms

Build atoms from `DOCS.md`, skipped criteria, and public TODO items.

- One criterion is one atom.
- Otherwise, the smallest independently verifiable DOCS statement is one atom; split a conjoint sentence per alternative.
- Otherwise, one public TODO item is one atom.
- A TODO item that mirrors a criterion is the same atom; the item loses. One atom cites every source that states it.

## Conflicts and ambiguities

A conflict is two promises with incompatible behavior. An ambiguity is a statement with two or more readings where at least one collides with an unfulfilled promise. Unfulfilled means not yet true in the repository, not merely untested. Discard a reading pinned by an active criterion or the current implementation; then it is not an ambiguity.

Interview one item at a time. Show both sides and offer options, each with its exact edit: one option per side or reading, always remove the other promise, and free-form. Wait for the answer. Never resolve anything yourself.

Collect every choice, then apply them once:

- May write `DOCS.md`, `TODO.md`, and a skipped criterion whose test does not exist.
- Never write an active criterion, a test, `README.md`, `CHANGELOG.md`, or `AGENTS.md`.
- Refuse to delete the last promise for an implemented public element.
- Re-derive the promise set and re-check conflicts. A new conflict joins the session; a repeated or cycling conflict stops the run.
- Never stage or commit.

An interrupted interview writes nothing.

## Dedupe

Before ranking, delete a public TODO item that mirrors a criterion when the criterion carries every value and relation it states. Keep implementation detail that survives; never rewrite the criterion.

## Ranking

Group atoms into packages by shared missing prerequisite, then shared artifact, then single atoms. Rank packages: ready before blocked; then highest unblocks; then smallest effort; then fewest risk flags; then spec-path order.

- **unblocks** — the package's atoms plus the atoms of packages whose only missing prerequisite it is.
- **effort** — atom count, then layers or artifacts touched, then a new runtime dependency.
- **risk flags** — mutates task data, adds a runtime dependency, changes a published contract, touches behavior no criterion can express.
- Blocked packages follow the ready ones with their blocker named. An unready promise is gap-only and never ranked.

The recommendation is the top ready package and its first atom, with one line of rationale.

## Verify and report

After applying, run `docker exec recurrator_dev make verify`. If it fails, report and leave the edits for inspection; do not repair.

Overwrite `./next-backlog-items.html` with a self-contained page; no external assets, no history. Its sections:

1. **Recommended** — package, first atom, rationale.
2. **Ranked** — rank, package, atoms, unblocks, effort, risk flags, ready or blocked.
3. **Gap** — each absent and present-unverified atom with state, source, evidence, and readiness; verified atoms as a count.
4. **Applied** — each resolution and dedupe edit, file and old to new.
5. **Blocked** — package and blocker.

Print the recommendation, the ranked table, and the page path. If nothing is missing and nothing is conflicting, say so and record the counts.

## Idempotency

The durable actions are the resolution edits, the dedupe deletions, and the page overwrite. Each requires that the conflict or duplicate exists; after it, it does not. A second run on the same committed state finds no conflict, deletes nothing, rewrites the same page, and reports the same ranking. The page is rewritten on every run by design, including a run with nothing to do.
