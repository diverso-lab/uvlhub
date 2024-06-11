#!/bin/bash

echo "(testing) Hostname: $MARIADB_HOSTNAME, Port: $MARIADB_PORT, User: $MARIADB_USER, Test DB: $MARIADB_TEST_DATABASE"

echo "MariaDB is up - creating test database if it doesn't exist"

# Create the test database if it does not exist
mariadb -h "$MARIADB_HOSTNAME" -P "$MARIADB_PORT" -u root -p"$MARIADB_ROOT_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS \`${MARIADB_TEST_DATABASE}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; GRANT ALL PRIVILEGES ON \`${MARIADB_TEST_DATABASE}\`.* TO '$MARIADB_USER'@'%'; FLUSH PRIVILEGES;"


echo "Test database created and privileges granted"
