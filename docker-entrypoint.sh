#!/bin/sh
set -e

mkdir -p /app/data

echo "--- Running migrations ---"
python manage.py migrate --noinput

echo "--- Populating reference data ---"
python populate_initial_data.py

echo "--- Populating singer models ---"
python populate_suno_models.py

echo "--- Starting server ---"
exec python manage.py runserver 0.0.0.0:8000
