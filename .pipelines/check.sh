#!/usr/bin/env bash
#
# Run the checks inside the development container.
# The container must already be running: this script starts nothing.

set -euo pipefail

CONTAINER="${PWD##*/}_dev"

if ! docker inspect "${CONTAINER}" > /dev/null 2>&1; then
    echo "The development container ${CONTAINER} is not running."
    echo "Start it, then push again."
    exit 1
fi

echo "Running make check and make tests in ${CONTAINER}."
docker exec "${CONTAINER}" make check tests
