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

PRODUCT_DIR="/workspace/${SPLENT_APP:-uvlhub_splent}"

if [ ! -d "$PRODUCT_DIR/node_modules/.bin" ]; then
    echo "    installing npm dependencies..."
    cd "$PRODUCT_DIR" && npm install --no-audit --no-fund --no-update-notifier
fi

splent feature:compile --watch

echo ""
