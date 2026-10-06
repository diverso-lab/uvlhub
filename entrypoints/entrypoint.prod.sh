#!/bin/bash

# ---------------------------------------------------------------------------
# Creative Commons CC BY 4.0 - SPLENT - Diverso Lab
# ---------------------------------------------------------------------------
# This script is licensed under the Creative Commons Attribution 4.0 
# International License.
# https://creativecommons.org/licenses/by/4.0/
# ---------------------------------------------------------------------------

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

  echo ""
  echo "  [$step]"
  bash "$script"
  rc=$?
  if [ $rc -ne 0 ]; then
  echo "  FAIL [$step] (rc=$rc)"
  exit $rc
  fi
  echo "  ok [$step]"
}

# ---------------------------------------------------------------------------
# Ensure the framework's dotenv loader picks up deploy vars, not dev vars.
# The Docker container already has the correct env vars from env_file;
# this syncs the on-disk .env so load_dotenv(override=True) is harmless.
# ---------------------------------------------------------------------------
ENV_DEPLOY="/workspace/uvlhub_splent/docker/.env.deploy"
ENV_FILE="/workspace/uvlhub_splent/docker/.env"
if [ -f "$ENV_DEPLOY" ]; then
  cp "$ENV_DEPLOY" "$ENV_FILE"
  echo "  synced .env.deploy -> .env"
fi

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
