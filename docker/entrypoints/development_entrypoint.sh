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

# Exit immediately if a command exits with a non-zero status
set -e

# Install fm_generator as editable package
echo "Installing fm_generator editable package..."
pip install --no-cache-dir -e ./fm_generator

# Build fm_generator wheel for Pyodide
echo "Building fm_generator wheel for Pyodide..."
pip install --no-cache-dir build

rm -f app/modules/generator/assets/js/fm_generator-*.whl
rm -rf fm_generator/dist fm_generator/build fm_generator/*.egg-info

python -m build --wheel ./fm_generator

cp fm_generator/dist/fm_generator-*.whl app/modules/generator/assets/js/

echo "fm_generator wheel copied:"
ls -l app/modules/generator/assets/js/fm_generator-*.whl

# Compile webpack files with hot reloading
rosemary webpack:compile --watch

# Create a specific database for testing by running a script
sh ./scripts/init-testing-db.sh

# Apply migrations
sh ./scripts/apply_migrations.sh

# Index the example UVLs
rosemary elasticsearch:reset

# Generates FM Fact Label visualization for example UVLs
rosemary factlabel:generate

# Start the Flask application with specified host and port, enabling reload and debug mode
exec flask run --host=0.0.0.0 --port=5000 --reload --debug
