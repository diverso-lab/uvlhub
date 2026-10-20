#!/bin/bash

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
