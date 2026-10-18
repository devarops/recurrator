#!/usr/bin/env bash
#
# Generate the modules built from the data repository, then run the command.
# The data directory defaults to the container runtime location and can be
# overridden with RECURRATOR_CONFIG_DIR (used by tests).

set -euo pipefail

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="${RECURRATOR_CONFIG_DIR:-/root/.config/recurrator}"

cd "${WORKDIR}"

"${WORKDIR}/src/create_config.sh" "${CONFIG_DIR}/config.json"
"${WORKDIR}/src/create_contexts.sh" "${CONFIG_DIR}/datapackage.json"

exec "$@"
