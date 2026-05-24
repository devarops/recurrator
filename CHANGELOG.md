# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `coins` field in `GET /task/{id}` JSON response.
- Context page now displays tasks sorted by coins descending.

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

No user-facing changes.

## [0.1.0] - 2026-05-09

### Added

- FastAPI REST API with endpoints:
  - `GET /task/` — list all task IDs
  - `GET /task/{task_id}` — get single task details
  - `POST /task/{task_id}/done` — mark task as done, returns updated
    skip_count and due_date, and recomputes the next due date
- CLI with `list-all-tasks` command

[unreleased]: https://github.com/devarops/recurrator/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/devarops/recurrator/releases/tag/v0.3.0
[0.2.0]: https://github.com/devarops/recurrator/releases/tag/v0.2.0
[0.1.0]: https://github.com/devarops/recurrator/releases/tag/v0.1.0
