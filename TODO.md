# Backlog

The design lives in `DESIGN.md`; this list is the build order. Each item states one outcome and its `Test:` line. It empties when the work is done.

- [ ] Align the suite with the multi-context contract
      Test: `make tests` and `mypy tests` pass with `contexts` arrays and the new context data; no test names the single-valued context column.
- [ ] Add the missing acceptance tests for the multi-context contract
      Test: `make verify` passes and no criterion in `specs/context_views.spec.toml`, `specs/tasks_views.spec.toml`, or `specs/task_edits.spec.toml` is skipped.
- [ ] Add one extra task when at least one and fewer than the work-in-progress limit are due
      Test: the six criteria in `specs/one_extra_task.spec.toml` are unskipped and `make verify` passes.
- [ ] Compute coins from the Glicko rating
      Test: `compute_coins` takes a rating; the boundary values in `DESIGN.md` pass; `make tests` passes.
- [ ] Delete tasks through the API
      Test: the eleven criteria in `specs/task_deletion.spec.toml` are unskipped and `make verify` passes.
- [ ] Add JSON schema validation for the config file
      Test: `make tests` rejects an invalid `config.json` against its schema.
- [ ] Set minimum and maximum recurrence days
      Test: `compute_recurrence_days` clamps to the configured bounds and `tests/test_compute.py` covers both ends.
- [ ] Move the relative date labels from the client into the API
      Test: the done, overdue, and upcoming labels come from API fields; the frontend performs no date arithmetic.
- [ ] Add blockers
      Test: a task is blocked while its blocker's row exists; a unit test covers the hidden state and the unblock after deletion.
- [ ] Add sub-tasks
      Test: completing any child completes its parent upward, never downward; a parent completed in the last two days is skipped; unit tests cover both.
