#!/bin/bash

set -e

echo ""

# The tests' own server, in memory, when the product has one; development's
# otherwise.
TEST_HOST="${MARIADB_TEST_HOSTNAME:-$MARIADB_HOSTNAME}"
for _ in $(seq 1 60); do
    if mariadb -h "$TEST_HOST" -P "3306" -u root -p"$MARIADB_ROOT_PASSWORD" -e "SELECT 1" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "    creating test database $MARIADB_TEST_DATABASE on $TEST_HOST..."

# Create the test database if it does not exist
mariadb -h "$TEST_HOST" -P "3306" -u root -p"$MARIADB_ROOT_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS \`${MARIADB_TEST_DATABASE}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; GRANT ALL PRIVILEGES ON \`${MARIADB_TEST_DATABASE}\`.* TO '$MARIADB_USER'@'%'; FLUSH PRIVILEGES;"

echo "    test database ready."

echo ""
