#!/bin/bash

set -Eeuo pipefail

if [ "$(id -u)" -eq 0 ]; then
  LOG_DIR="/var/log/splent"
else
  if [ -z "${SPLENT_HOST_PROJECT_DIR:-}" ]; then
    echo "  error: SPLENT_HOST_PROJECT_DIR not defined."
    exit 1
  fi
  LOG_DIR="${SPLENT_HOST_PROJECT_DIR}/.splent/logs"
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

# A step that needs nothing from the ones after it runs alongside them. Its
# output waits in a file so the two never interleave, and join_step prints it
# and fails the startup as run_step would.
start_step () {
  BG_STEP="$1"
  BG_LOG="$(mktemp)"
  BG_STARTED=$SECONDS
  bash "$2" >"$BG_LOG" 2>&1 &
  BG_PID=$!
}

join_step () {
  local rc=0
  wait "$BG_PID" || rc=$?
  echo ""
  echo "  [$BG_STEP]"
  cat "$BG_LOG"
  rm -f "$BG_LOG"
  if [ $rc -ne 0 ]; then
    echo "  FAIL [$BG_STEP] (rc=$rc)"
    exit $rc
  fi
  echo "  ok [$BG_STEP] ($((SECONDS - BG_STARTED))s, alongside the database steps)"
}

# ---------------------------------------------------------------------------
# MAIN STARTUP SEQUENCE
# ---------------------------------------------------------------------------
run_step "00_core_requirements_dev" "/workspace/uvlhub/scripts/00_core_requirements_dev.sh"
run_step "00_install_features"      "/workspace/uvlhub/scripts/00_install_features.sh"
# npm and webpack need no database, and the database steps need no assets.
start_step "01_compile_assets"      "/workspace/uvlhub/scripts/01_compile_assets.sh"
run_step "02_0_db_wait"             "/workspace/uvlhub/scripts/02_0_db_wait_connection.sh"
run_step "02_1_db_create_test"      "/workspace/uvlhub/scripts/02_1_db_create_db_test.sh"
run_step "02_2_db_splent_migrations" "/workspace/uvlhub/scripts/02_2_db_create_splent_migrations.sh"
run_step "03_init_migrations"       "/workspace/uvlhub/scripts/03_initialize_migrations.sh"
run_step "04_handle_migrations"     "/workspace/uvlhub/scripts/04_handle_migrations.sh"
join_step
run_step "05_0_start_app_dev"       "/workspace/uvlhub/scripts/05_0_start_app_dev.sh"

echo ""
echo "  entrypoint finished"
