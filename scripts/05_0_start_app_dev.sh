#!/bin/bash

set -e

echo ""

# Kill any previous Flask/watchmedo processes to avoid port conflicts and stale code
pkill -f "watchmedo.*auto-restart" 2>/dev/null || true
pkill -f "flask run" 2>/dev/null || true
sleep 1

# The app runs as the workspace's owner, as the tests do, not as root. What
# it wrote as root stayed root's: bytecode and uploads in the working copies,
# which the owner's next release could not rewrite, and a session store under
# /tmp that the tests, run as the owner, could not write to. What root left
# there before goes back first. A workspace root owns, or an image without
# setpriv, keeps root.
as_owner=()
owner_uid="$(stat -c %u /workspace)"
owner_gid="$(stat -c %g /workspace)"
if [ "$(id -u)" = 0 ] && [ "$owner_uid" != 0 ] && command -v setpriv >/dev/null; then
    owner="$owner_uid:$owner_gid"
    for path in /workspace/uvlhub_splent /workspace/uploads; do
        [ -e "$path" ] || continue
        find -H "$path" -name node_modules -prune -o -user 0 \
            -exec chown -h "$owner" {} + 2>/dev/null || true
    done
    find /tmp -mindepth 1 -maxdepth 1 -user 0 -exec chown -R "$owner" {} + 2>/dev/null || true
    home="/tmp/splent-home-$owner_uid"
    mkdir -p "$home" && chown "$owner" "$home"
    as_owner=(setpriv --reuid="$owner_uid" --regid="$owner_gid" --clear-groups
              env HOME="$home" USER=splent LOGNAME=splent)
fi

# Flask's reloader watches every directory on sys.path and of every module
# loaded, and the product's whole directory, for *.py, *.pyc and *.zip. So a
# zip the app wrote under src/instance restarted it in the middle of the
# request writing it, and so did bytecode written by a test run and edits to
# the CLI by anyone. What the app writes (instance, uploads), what builds
# leave (node_modules, bytecode) and the CLI's checkout do not count.
# Bytecode is left out by its folder: "*.pyc" and "*.zip" are patterns the
# reloader watches, and watchdog 4 and later refuse a pattern both watched
# and excluded, which killed the reloader's thread at the first change.
EXCLUDE="*/instance/*:*/uploads/*:*/node_modules/*:*/__pycache__/*:/workspace/splent_cli/*"

"${as_owner[@]}" watchmedo auto-restart \
    --directory=/workspace/uvlhub_splent/src/uvlhub_splent \
    --pattern=*.py \
    --ignore-patterns="*/instance/*;*/uploads/*" \
    --recursive \
    -- flask run --host=0.0.0.0 --port=5000 --debug --exclude-patterns "$EXCLUDE" \
    >> /var/log/entrypoint.log 2>&1 &

echo ""
