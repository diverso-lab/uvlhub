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

echo "    waiting for $MARIADB_HOSTNAME:3306..."

MAX_RETRIES=60
RETRY=0

while ! mariadb -h "$MARIADB_HOSTNAME" -P "3306" -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" -e 'SELECT 1' >/dev/null 2>&1; do
  RETRY=$((RETRY + 1))
  if [ "$RETRY" -ge "$MAX_RETRIES" ]; then
    echo "    MariaDB unavailable after $MAX_RETRIES retries, aborting."
    exit 1
  fi
  echo "    waiting... (retry $RETRY/$MAX_RETRIES)"
  sleep 1
done

echo "    MariaDB is up."
exec "$@"

