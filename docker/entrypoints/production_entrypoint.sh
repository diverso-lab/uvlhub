#!/bin/sh
set -e

sh ./scripts/wait-for-db.sh

# if the migrations folder does not exist, creates it and initialises the migrations
if [ ! -d "migrations" ]; then
    flask db init
fi

flask db migrate
flask db upgrade

exec gunicorn --bind 0.0.0.0:5000 app:app --log-level info --timeout 3600
