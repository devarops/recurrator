#!/bin/bash
set -euo pipefail

DATAPACKAGE="${1:-/root/.config/recurrator/datapackage.json}"
OUTPUT="recurrator/_contexts.py"

if [ ! -f "$DATAPACKAGE" ]; then
    DATAPACKAGE="tests/data/datapackage.json"
fi

CONTEXTS=$(jq -r '.resources[0].schema.fields[] | select(.name == "context").constraints.enum[]' "$DATAPACKAGE")

cat > "$OUTPUT" <<- EOF
# This file is auto-generated. Do not edit manually.
# Regenerate with: make install

from enum import Enum


class Context(Enum):
    """Valid task contexts from datapackage.json."""

EOF

for ctx in $CONTEXTS; do
    upper=$(echo "$ctx" | tr '[:lower:]' '[:upper:]')
    echo "    $upper = \"$ctx\"" >> "$OUTPUT"
done
