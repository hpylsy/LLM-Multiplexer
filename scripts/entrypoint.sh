#!/bin/sh
set -e

echo "[entrypoint] Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
RETRIES=30
until nc -z "$POSTGRES_HOST" "$POSTGRES_PORT" || [ $RETRIES -eq 0 ]; do
  echo "[entrypoint] Waiting... ($RETRIES retries left)"
  RETRIES=$((RETRIES - 1))
  sleep 2
done

if [ $RETRIES -eq 0 ]; then
  echo "[entrypoint] ERROR: PostgreSQL not available after 60s, exiting."
  exit 1
fi

echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput

echo "[entrypoint] Starting Gunicorn..."
exec gunicorn lab_portal.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
