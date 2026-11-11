#!/bin/bash

set -e

echo ""

WORKERS=${GUNICORN_WORKERS:-$(( 2 * $(nproc) + 1 ))}
TIMEOUT=${GUNICORN_TIMEOUT:-120}

# The production profile, spelled out: DEBUG off and SECRET_KEY required
# from the environment (the framework would also derive it from SPLENT_ENV).
exec gunicorn --bind 0.0.0.0:5000 \
    'uvlhub:create_app("production")' \
    --workers "$WORKERS" \
    --timeout "$TIMEOUT" \
    --access-logfile - \
    --log-level info
