#!/bin/sh
# Exit immediately if a command exits with a non-zero status
set -e

# Install Rosemary
pip install -e ./

# Wait for the database to be ready by running a script
sh ./scripts/wait-for-db.sh

# Create a specific database for testing by running a script
sh ./scripts/init-testing-db.sh

# Initialize migrations only if the migrations directory doesn't exist
if [ ! -d "migrations" ]; then
    # Initialize the migration repository
    flask db init
fi

# Run the migration process to apply the database schema changes
rosemary db:migrate

# Seed the database with initial data, reset if needed
rosemary db:seed -y --reset

# Start the Flask application with specified host and port, enabling reload and debug mode
exec flask run --host=0.0.0.0 --port=5000 --reload --debug
