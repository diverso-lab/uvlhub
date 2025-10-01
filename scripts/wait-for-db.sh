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

set -e

TIMEOUT=${TIMEOUT:-60}
START_TIME=$(date +%s)

echo "🚀 Starting wait-for-db.sh"
echo "Hostname: $MARIADB_HOSTNAME, Port: $MARIADB_PORT, User: $MARIADB_USER"
echo "⏱️ Timeout set to $TIMEOUT seconds"

while ! mariadb \
    -h "$MARIADB_HOSTNAME" \
    -P "$MARIADB_PORT" \
    -u"$MARIADB_USER" \
    -p"$MARIADB_PASSWORD" \
    -e 'SELECT 1' > /dev/null 2>&1; do

  CURRENT_TIME=$(date +%s)
  ELAPSED=$((CURRENT_TIME - START_TIME))

  if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "❌ Timeout reached after $ELAPSED seconds. MariaDB is still unavailable."
    exit 1
  fi

  echo "⏳ MariaDB is unavailable - sleeping"
  sleep 1
done

echo "✅ MariaDB is up after $(( $(date +%s) - START_TIME )) seconds - executing command"
exec "$@"