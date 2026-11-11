#!/bin/bash

set -e

echo ""

PRODUCT_DIR="/workspace/${SPLENT_APP:-uvlhub}"

if [ ! -d "$PRODUCT_DIR/node_modules/.bin" ]; then
    echo "    installing npm dependencies..."
    cd "$PRODUCT_DIR" && npm install --no-audit --no-fund --no-update-notifier
fi

# webpack writes each feature's bundle into its copy, so it runs as the
# workspace's owner, as the app does (05_0_start_app_dev.sh).
as_owner=()
owner_uid="$(stat -c %u /workspace)"
owner_gid="$(stat -c %g /workspace)"
if [ "$(id -u)" = 0 ] && [ "$owner_uid" != 0 ] && command -v setpriv >/dev/null; then
    home="/tmp/splent-home-$owner_uid"
    mkdir -p "$home" && chown "$owner_uid:$owner_gid" "$home"
    as_owner=(setpriv --reuid="$owner_uid" --regid="$owner_gid" --clear-groups
              env HOME="$home" USER=splent LOGNAME=splent)
fi

"${as_owner[@]}" splent feature:compile --watch

echo ""
