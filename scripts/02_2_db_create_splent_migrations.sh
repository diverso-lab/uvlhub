#!/bin/bash

#
# Creates the splent_migrations table used by SPLENT to track the last
# applied migration revision per feature.
#
# Columns:
#   feature         the feature name as declared in pyproject.toml (PRIMARY KEY)
#   last_migration  the last Alembic revision applied for that feature
#
# This script is idempotent: running it multiple times is safe.

set -e

echo ""

mariadb \
    -u "$MARIADB_USER" \
    -p"$MARIADB_PASSWORD" \
    -h "$MARIADB_HOSTNAME" \
    -P 3306 \
    "$MARIADB_DATABASE" <<'SQL'
CREATE TABLE IF NOT EXISTS `splent_migrations` (
    `feature`        VARCHAR(255) NOT NULL,
    `last_migration` VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY (`feature`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
SQL

echo "    splent_migrations table ready."
