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

echo "    creating test database $MARIADB_TEST_DATABASE..."

# Create the test database if it does not exist
mariadb -h "$MARIADB_HOSTNAME" -P "3306" -u root -p"$MARIADB_ROOT_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS \`${MARIADB_TEST_DATABASE}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; GRANT ALL PRIVILEGES ON \`${MARIADB_TEST_DATABASE}\`.* TO '$MARIADB_USER'@'%'; FLUSH PRIVILEGES;"

echo "    test database ready."

echo ""
