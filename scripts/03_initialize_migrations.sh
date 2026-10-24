#!/bin/bash

set -e

echo ""

# The one migration of the start. db:upgrade holds a lock of the database
# server while it runs (GET_LOCK), so a second replica starting at the same
# time waits for this one and then finds nothing left to apply.
#
# Whether the database was empty is decided by db:upgrade too, under that
# lock and before the first table is created, and left in the marker for
# 04_handle_migrations. Counting tables here, outside the lock, let two
# replicas both find the database empty and both seed it.
FRESH_DB_MARKER=/tmp/splent_fresh_db
rm -f "$FRESH_DB_MARKER"

# SPLENT_MIGRATE_ON_START says whether the start migrates at all (PL-7):
#   upgrade  the default: apply what is pending, as below
#   check    apply nothing, and refuse to start when a feature's schema is
#            not at the head of its migrations. For a deploy agent that
#            migrates in a step of its own (splent_feature_autodeploy runs
#            db:upgrade in a one-off container first): the web container
#            then never migrates, and never serves on a schema its code is
#            ahead of
#   off      apply nothing and check nothing
# A database that is migrated elsewhere is never seeded here either.
mode=$(printf '%s' "${SPLENT_MIGRATE_ON_START:-upgrade}" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')
case "$mode" in
    upgrade|true|on|yes|1) mode=upgrade ;;
    check) ;;
    off|false|no|0) mode=off ;;
    *)
        echo "    SPLENT_MIGRATE_ON_START is '${SPLENT_MIGRATE_ON_START}'; it is upgrade, check or off"
        exit 1
        ;;
esac

if [ "$mode" = "off" ]; then
    echo "    SPLENT_MIGRATE_ON_START=off: nothing is migrated or checked"
    echo ""
    exit 0
fi

if [ "$mode" = "check" ]; then
    echo "    SPLENT_MIGRATE_ON_START=check: nothing is migrated, the schema has to be at head"
    # db:status --check came with this script; a CLI older than it cannot
    # tell, and a start that cannot tell does not serve.
    if ! python3 -c "import sys; from splent_cli.commands.database.db_status import db_status; sys.exit(not any(p.name == 'check' for p in db_status.params))" 2>/dev/null; then
        echo "    this CLI has no db:status --check, so the schema cannot be checked"
        exit 1
    fi
    splent db:status --check
    echo ""
    exit 0
fi

echo "    applying pending migrations..."
# The CLI here is the one [tool.splent.runtime] pins, which can be older
# than this script: product:sync-template brings the script in as soon as
# the workspace CLI has it. A CLI without the lock (no migration_lock module)
# knows no --fresh-marker and stopped the start on it, so it migrates as it
# did before, with the tables counted here.
if python3 -c "import importlib.util, sys; sys.exit(importlib.util.find_spec('splent_cli.utils.migration_lock') is None)"; then
    splent db:upgrade --fresh-marker "$FRESH_DB_MARKER"
else
    echo "    this CLI has no migration lock, so replicas must not start together"
    TABLE_COUNT=$(mariadb -u "$MARIADB_USER" -p"$MARIADB_PASSWORD" -h "$MARIADB_HOSTNAME" -P 3306 -D "$MARIADB_DATABASE" -sse \
        "SELECT COUNT(*) FROM information_schema.tables
         WHERE table_schema = '$MARIADB_DATABASE'
         AND table_name NOT IN ('splent_migrations');")
    if [ "$TABLE_COUNT" -eq 0 ]; then
        touch "$FRESH_DB_MARKER"
    fi
    splent db:upgrade
fi

echo ""
