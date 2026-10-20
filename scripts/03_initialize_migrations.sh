#!/bin/bash

set -e

echo ""

# Whether the database is fresh has to be decided HERE, before the first
# upgrade creates the tables. 04_handle_migrations used to count tables after
# this script had already created them, always found some, and so never
# seeded: RUN_DB_SEED=true did nothing and nobody could log in.
FRESH_DB_MARKER=/tmp/splent_fresh_db
rm -f "$FRESH_DB_MARKER"
TABLE_COUNT=$(mariadb -u "$MARIADB_USER" -p"$MARIADB_PASSWORD" -h "$MARIADB_HOSTNAME" -P 3306 -D "$MARIADB_DATABASE" -sse \
    "SELECT COUNT(*) FROM information_schema.tables
     WHERE table_schema = '$MARIADB_DATABASE'
     AND table_name NOT IN ('splent_migrations');")
if [ "$TABLE_COUNT" -eq 0 ]; then
    touch "$FRESH_DB_MARKER"
fi

splent db:upgrade

echo ""
