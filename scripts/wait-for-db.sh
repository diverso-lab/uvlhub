#!/bin/bash

# ---------------------------------------------------------------------------
# Creative Commons CC BY 4.0 - David Romero - Diverso Lab
# ---------------------------------------------------------------------------
# This script is licensed under the Creative Commons Attribution 4.0 
# International License. You are free to share and adapt the material 
# as long as appropriate credit is given, a link to the license is provided, 
# and you indicate if changes were made.
#
# For more details, visit:
# https://creativecommons.org/licenses/by/4.0/
# ---------------------------------------------------------------------------

echo "Starting wait-for-db.sh"
echo "Hostname: $MARIADB_HOSTNAME, Port: $MARIADB_PORT, User: $MARIADB_USER"

while ! mariadb -h "$MARIADB_HOSTNAME" -P "$MARIADB_PORT" -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" -e 'SELECT 1'; do
  echo "MariaDB is unavailable - sleeping"
  sleep 1
done

echo "MariaDB is up - executing command"
exec "$@"
