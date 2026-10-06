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
#
# Creates the splent_migrations table used by SPLENT to track the last
# applied migration revision per feature.
#
# Columns:
#   feature        — feature name as declared in pyproject.toml (PRIMARY KEY)
#   last_migration — last Alembic revision applied for that feature
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
