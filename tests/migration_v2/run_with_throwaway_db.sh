#!/usr/bin/env bash
#
# Run the product's own tests with a MariaDB of their own for the migrator's.
#
# The migrator drops and creates whole databases, so its tests never run on
# the development database or the shared test one. This starts a throwaway
# server of the product's major version on the web container's network,
# names it in MIGRATION_V2_TEST_DB_HOST and MIGRATION_V2_TEST_DB_ROOT_PASSWORD,
# which product:test hands the tests ([tool.splent.test] env), and removes
# it however the run ends.
#
# From the CLI container. Without arguments it runs every test of the
# product, as product:test --own-tests does, so it takes the shared test
# database's lock as any product:test run does:
#
#     flock /tmp/splent-test.lock bash uvlhub_splent/tests/migration_v2/run_with_throwaway_db.sh
#
# With arguments it runs the migrator's tests alone, with those pytest
# arguments, in the web container; they need no lock:
#
#     bash uvlhub_splent/tests/migration_v2/run_with_throwaway_db.sh -q -k preflight
#
set -euo pipefail

PRODUCT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
PRODUCT=$(basename "$PRODUCT_DIR")
WEB=${MIGRATION_V2_WEB_CONTAINER:-${PRODUCT}_web}
IMAGE=${MIGRATION_V2_TEST_DB_IMAGE:-mariadb:11.4}
NETWORK=$(docker inspect "$WEB" --format '{{range $name, $_ := .NetworkSettings.Networks}}{{$name}} {{end}}' | awk '{print $1}')
NAME="uvlhub_migv2_test_$(date +%s)_$RANDOM"
PASSWORD=$(od -An -N16 -tx1 /dev/urandom | tr -d ' \n')

cleanup() { docker rm -f -v "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT INT TERM

# Small: other containers share the machine.
docker run -d --rm --name "$NAME" --network "$NETWORK" --memory 768m \
    -e MARIADB_ROOT_PASSWORD="$PASSWORD" "$IMAGE" \
    --innodb-buffer-pool-size=64M --performance-schema=OFF \
    --skip-name-resolve --max-connections=60 >/dev/null

export MIGRATION_V2_TEST_DB_HOST="$NAME"
export MIGRATION_V2_TEST_DB_ROOT_PASSWORD="$PASSWORD"

if [ "$#" -eq 0 ]; then
    cd "$PRODUCT_DIR/.."
    splent product:test --own-tests --product "$PRODUCT"
else
    OWNER=$(stat -c '%u:%g' "$PRODUCT_DIR")
    docker exec -i -u "$OWNER" \
        -e HOME=/tmp/migration_v2_home -e USER=splent -e LOGNAME=splent \
        -e PYTHONDONTWRITEBYTECODE=1 \
        -e MIGRATION_V2_TEST_DB_HOST -e MIGRATION_V2_TEST_DB_ROOT_PASSWORD \
        "$WEB" bash -lc 'mkdir -p "$HOME" && cd /workspace/'"$PRODUCT"' && python -m pytest tests/migration_v2 -p no:cacheprovider "$@"' -- "$@"
fi
