#!/bin/sh
set -e

cd /app/backend
alembic upgrade head

uvicorn app.main:app --host 127.0.0.1 --port 8000 &

nginx -g 'daemon off;'
