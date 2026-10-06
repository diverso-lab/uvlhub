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

# 03_initialize_migrations recorded whether the database was empty before it
# created any table; counting tables here would always find the ones it made.
FRESH_DB_MARKER=/tmp/splent_fresh_db

echo "    applying pending migrations..."
splent db:upgrade

if [ -f "$FRESH_DB_MARKER" ]; then
    rm -f "$FRESH_DB_MARKER"
    if [ "$RUN_DB_SEED" = "true" ]; then
        echo "    fresh database, seeding..."
        splent db:seed -y
    fi
fi

echo ""
