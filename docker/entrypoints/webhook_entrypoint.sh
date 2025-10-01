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

# Updates requirements.txt
pip install --no-cache-dir --upgrade pip
pip install --pre -r requirements.txt

# Updates Rosemary
pip install -e ./

# Compile webpack files
rosemary webpack:compile

# Apply migrations
sh ./scripts/apply_migrations.sh

# Start the application using Gunicorn, binding it to port 5000
# Set the logging level to info and the timeout to 3600 seconds
exec gunicorn --workers 3 --bind 0.0.0.0:5000 app:app --log-level info --timeout 3600
