#!/bin/bash

# ---------------------------------------------------------------------------
# Creative Commons CC BY 4.0 - SPLENT - Diverso Lab
# ---------------------------------------------------------------------------
# This script is licensed under the Creative Commons Attribution 4.0 
# International License. You are free to share and adapt the material 
# as long as appropriate credit is given, a link to the license is provided, 
# and you indicate if changes were made.
#
# For more details, visit:
# https://creativecommons.org/licenses/by/4.0/
# ---------------------------------------------------------------------------

set -e

echo ""

# Kill any previous Flask/watchmedo processes to avoid port conflicts and stale code
pkill -f "watchmedo.*auto-restart" 2>/dev/null || true
pkill -f "flask run" 2>/dev/null || true
sleep 1

watchmedo auto-restart \
    --directory=/workspace/uvlhub_splent/src/uvlhub_splent \
    --pattern=*.py \
    --recursive \
    -- flask run --host=0.0.0.0 --port=5000 --debug >> /var/log/entrypoint.log 2>&1 &

echo ""
