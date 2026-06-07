#!/bin/bash
# Generate recurrator/_config.py from config.json.
# Falls back to hardcoded defaults if config.json is missing.
set -euo pipefail

CONFIG_FILE="${1:-/root/.config/recurrator/config.json}"
OUTPUT="recurrator/_config.py"

if [ -f "$CONFIG_FILE" ]; then
    CONFIG_SOURCE="$CONFIG_FILE"
elif [ -f "tests/data/config.json" ]; then
    CONFIG_SOURCE="tests/data/config.json"
else
    CONFIG_SOURCE=""
fi

cat > "$OUTPUT" <<- 'EOF'
# This file is auto-generated. Do not edit manually.
# Regenerate with: make install

EOF

if [ -n "$CONFIG_SOURCE" ]; then
    jq -r '
        to_entries[] |
        "\(.key | ascii_upcase) = \(.value | @json)"
    ' "$CONFIG_SOURCE" >> "$OUTPUT"
else
    cat >> "$OUTPUT" <<- 'EOF'
API_BASE_URL = "http://api:8000"
DEFAULT_RECURRENCE_DAYS = 14
DEFAULT_TASKS_CSV_PATH = "/root/.config/recurrator/tasks.csv"
MIN_DAYS_GAP = 2
EOF
fi
