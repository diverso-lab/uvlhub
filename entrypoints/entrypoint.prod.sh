#!/bin/bash

set -Eeuo pipefail

# ---------------------------------------------------------------------------
# The app runs as the unprivileged user the image creates, never as root.
# The container starts as root for one thing only: whatever root owns in the
# named volumes mounted into it (all of it, on a deployment an older image
# filled as root; a file a `docker exec` left, later) is handed to that user.
# Then this script runs itself again as that user, and so do the migrations
# and gunicorn.
# ---------------------------------------------------------------------------
APP_USER="splent"
LOG_DIR="/var/log/splent"
if [ "$(id -u)" -eq 0 ] && id "$APP_USER" >/dev/null 2>&1; then
  while read -r mount_point; do
    if [ -n "$(find "$mount_point" ! -user "$APP_USER" -print -quit)" ]; then
      echo "  handing what root owns in $mount_point to $APP_USER"
      find "$mount_point" ! -user "$APP_USER" -exec chown -h "$APP_USER:$APP_USER" {} +
    fi
  done < <(awk '$4 ~ /\/volumes\/[^/]+\/_data$/ {print $5}' /proc/self/mountinfo)
  mkdir -p "$LOG_DIR"
  chown "$APP_USER:$APP_USER" "$LOG_DIR"
  export HOME="/home/$APP_USER"
  exec setpriv --reuid="$APP_USER" --regid="$APP_USER" --init-groups bash "$0" "$@"
fi

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/entrypoint.log"
touch "$LOG_FILE"

exec > >(tee -a "$LOG_FILE") 2>&1

echo ""

_last_cmd=""
trap '_last_cmd=$BASH_COMMAND' DEBUG
trap 'rc=$?; echo "  FAIL (rc=$rc) while running: ${_last_cmd}"; echo "    at ${BASH_SOURCE[0]}:${LINENO}"; exit $rc' ERR

run_step () {
  local step="$1"
  local script="$2"

  local started=$SECONDS

  echo ""
  echo "  [$step]"
  bash "$script"
  rc=$?
  if [ $rc -ne 0 ]; then
  echo "  FAIL [$step] (rc=$rc)"
  exit $rc
  fi
  echo "  ok [$step] ($((SECONDS - started))s)"
}

# The container's settings are its environment, which the deploy bundle hands
# it from deploy/.env (env_file). The image carries no env file of its own.

# ---------------------------------------------------------------------------
# MAIN STARTUP SEQUENCE
# ---------------------------------------------------------------------------
run_step "02_0_db_wait"             "/workspace/uvlhub_splent/scripts/02_0_db_wait_connection.sh"
run_step "02_2_db_splent_migrations" "/workspace/uvlhub_splent/scripts/02_2_db_create_splent_migrations.sh"
run_step "03_init_migrations"       "/workspace/uvlhub_splent/scripts/03_initialize_migrations.sh"
run_step "04_handle_migrations"     "/workspace/uvlhub_splent/scripts/04_handle_migrations.sh"
run_step "05_1_start_app_prod"      "/workspace/uvlhub_splent/scripts/05_1_start_app_prod.sh"

echo ""
echo "  entrypoint finished"
