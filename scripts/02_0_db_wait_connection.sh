#!/bin/bash

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

