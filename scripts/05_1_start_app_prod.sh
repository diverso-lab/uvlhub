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

WORKERS=${GUNICORN_WORKERS:-$(( 2 * $(nproc) + 1 ))}
TIMEOUT=${GUNICORN_TIMEOUT:-120}

# The production profile, spelled out: DEBUG off and SECRET_KEY required
# from the environment (the framework would also derive it from SPLENT_ENV).
exec gunicorn --bind 0.0.0.0:5000 \
    'uvlhub_splent:create_app("production")' \
    --workers "$WORKERS" \
    --timeout "$TIMEOUT" \
    --access-logfile - \
    --log-level info
