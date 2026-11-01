#!/bin/bash

set -e

echo ""

echo "    creating test database $MARIADB_TEST_DATABASE..."

# Create the test database if it does not exist
mariadb -h "$MARIADB_HOSTNAME" -P "3306" -u root -p"$MARIADB_ROOT_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS \`${MARIADB_TEST_DATABASE}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; GRANT ALL PRIVILEGES ON \`${MARIADB_TEST_DATABASE}\`.* TO '$MARIADB_USER'@'%'; FLUSH PRIVILEGES;"

echo "    test database ready."

echo ""
