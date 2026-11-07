#!/usr/bin/env bash
#
# Run the acceptance checks in the develop image.
# The app image must already exist; this script does not build it, and the
# develop image layers on top of it.

set -euo pipefail

docker compose --profile develop run --rm develop make verify
