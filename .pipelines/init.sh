#!/usr/bin/env bash
#
# Point git at the repository hooks so the pre-push check runs.
# Safe to run more than once.

set -euo pipefail

git config core.hooksPath .githooks
git config --get core.hooksPath
