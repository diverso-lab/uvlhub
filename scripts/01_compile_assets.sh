#!/bin/bash

set -e

echo ""

PRODUCT_DIR="/workspace/${SPLENT_APP:-uvlhub_splent}"

if [ ! -d "$PRODUCT_DIR/node_modules/.bin" ]; then
    echo "    installing npm dependencies..."
    cd "$PRODUCT_DIR" && npm install --no-audit --no-fund --no-update-notifier
fi

splent feature:compile --watch

echo ""
