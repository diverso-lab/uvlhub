#!/bin/sh

echo "Hostname: $MARIADB_HOSTNAME, Port: $MARIADB_PORT, User: $MARIADB_USER"

until mysql -h "$MARIADB_HOSTNAME" -P "$MARIADB_PORT" -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" -e 'SELECT 1' &> /dev/null
do
  echo "MariaDB is unavailable - sleeping"
  sleep 1
done

echo "MariaDB is up - executing command"
exec "$@"
