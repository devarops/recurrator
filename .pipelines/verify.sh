#!/usr/bin/env bash
#
# Run the qed acceptance spec in the develop image.
# The app image must already exist; this script does not build it.

set -euo pipefail

docker compose --profile develop run --rm develop make verify
