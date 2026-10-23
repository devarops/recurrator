# Changelog

This file records every change to the API entry points listed in `DOCS.md`, which form the Public Interface; changes unrelated to those entry points are not listed.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- `GET /task/{id}` now returns **404 Not Found** with the standard error
  envelope `{"error": "Task not found"}` when the task ID is not found,
  instead of serializing an HTTP 200 array response.

## [0.6.0] - 2026-06-07

### Added

- `GET /context/{context_id}` now returns prioritized task IDs, limited by
  work-in-progress capacity. Surplus non-starred tasks are automatically skipped.

### Changed

- The skip-date column in the task data file read by `GET /task/` was renamed
  to `skip_date`.

## [0.5.0] - 2026-05-24

### Added

- `POST /task/{id}/done` now returns **409 Conflict** when the task was already
  completed today or yesterday. The completion is rejected and the task remains
  unchanged.

## [0.4.0] - 2026-05-24

### Added

- `coins` field in `GET /task/{id}` JSON response.

### Fixed

- `POST /task/{id}/done` completion dates now use the `America/Los_Angeles`
  timezone instead of UTC, preventing off-by-one-day errors for Western
  Hemisphere users.

## [0.3.0] - 2026-05-10

### Added

- `GET /context/` — endpoint returning unique context names from due tasks
- `GET /context/{context_id}` — endpoint returning due task IDs filtered by context

### Changed

- **BREAKING**: `GET /task/` now returns raw task ID integers (`[1, 2, 3]`) instead
  of wrapped objects (`[{"id": 1}, ...]`)

## [0.2.0] - 2026-05-09

- (Empty release; no changes since v0.1.0)

## [0.1.0] - 2026-05-09

### Added

- FastAPI REST API with endpoints:
  - `GET /task/` — list all task IDs
  - `GET /task/{task_id}` — get single task details
  - `POST /task/{task_id}/done` — mark task as done, returns updated
    skip_count and due_date, and recomputes the next due date

[unreleased]: https://github.com/devarops/recurrator/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/devarops/recurrator/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/devarops/recurrator/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/devarops/recurrator/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/devarops/recurrator/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/devarops/recurrator/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/devarops/recurrator/releases/tag/v0.1.0
