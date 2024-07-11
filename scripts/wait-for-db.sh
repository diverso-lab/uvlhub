#!/bin/sh

echo "Starting wait-for-db.sh"
echo "Hostname: $MARIADB_HOSTNAME, Port: $MARIADB_PORT, User: $MARIADB_USER"

while ! mariadb -h "$MARIADB_HOSTNAME" -P "$MARIADB_PORT" -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" -e 'SELECT 1'; do
  echo "MariaDB is unavailable - sleeping"
  sleep 1
done

echo "MariaDB is up - executing command"
exec "$@"
