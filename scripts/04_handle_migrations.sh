#!/bin/bash

set -e

echo ""

# 03_initialize_migrations has applied the migrations, once, and recorded
# whether the database was empty before it did. Nothing is migrated here:
# a second db:upgrade on every start found nothing to do and took the time
# of building the app again.
FRESH_DB_MARKER=/tmp/splent_fresh_db

# SPLENT_ENV as the framework reads it: stripped, lowercased, and the long
# spelling mapped to the short one.
env=$(printf '%s' "${SPLENT_ENV:-}" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')
case "$env" in production) env=prod ;; esac

if [ -f "$FRESH_DB_MARKER" ]; then
    rm -f "$FRESH_DB_MARKER"
    if [ "$RUN_DB_SEED" = "true" ]; then
        if [ "$env" = "prod" ]; then
            # The seeders write demo data, which a production database never
            # gets, and db:seed refuses production anyway.
            echo "    fresh database; RUN_DB_SEED=true is ignored in production"
        else
            echo "    fresh database, seeding..."
            splent db:seed -y
        fi
    fi
fi

echo ""
