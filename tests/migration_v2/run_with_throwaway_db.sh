#!/usr/bin/env bash
#
# Run the migrator's tests (tests/migration_v2) on a MariaDB of their own.
#
# The migrator drops and creates whole databases, so its tests never run on
# the development database or the shared test one. This starts a throwaway
# server of the product's major version on the web container's network,
# runs the tests in the web container (where the features are installed),
# as the workspace's owner, and removes the server however the run ends.
#
# From the CLI container, or any host with docker and the workspace:
#
#     bash uvlhub_splent/tests/migration_v2/run_with_throwaway_db.sh [pytest args]
#
set -euo pipefail

WEB=${MIGRATION_V2_WEB_CONTAINER:-uvlhub_splent_web}
IMAGE=${MIGRATION_V2_TEST_DB_IMAGE:-mariadb:11.4}
PRODUCT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
NETWORK=$(docker inspect "$WEB" --format '{{range $name, $_ := .NetworkSettings.Networks}}{{$name}} {{end}}' | awk '{print $1}')
NAME="uvlhub_migv2_test_$(date +%s)_$RANDOM"
PASSWORD=$(od -An -N16 -tx1 /dev/urandom | tr -d ' \n')
OWNER=$(stat -c '%u:%g' "$PRODUCT_DIR")

cleanup() { docker rm -f -v "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT INT TERM

# Small: other containers share the machine.
docker run -d --rm --name "$NAME" --network "$NETWORK" --memory 768m \
    -e MARIADB_ROOT_PASSWORD="$PASSWORD" "$IMAGE" \
    --innodb-buffer-pool-size=64M --performance-schema=OFF \
    --skip-name-resolve --max-connections=60 >/dev/null

docker exec -i -u "$OWNER" \
    -e HOME=/tmp/migration_v2_home -e USER=splent -e LOGNAME=splent \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e MIGRATION_V2_TEST_DB_HOST="$NAME" \
    -e MIGRATION_V2_TEST_DB_ROOT_PASSWORD="$PASSWORD" \
    "$WEB" bash -lc 'mkdir -p "$HOME" && cd /workspace/uvlhub_splent && python -m pytest tests/migration_v2 -p no:cacheprovider "$@"' -- "$@"
