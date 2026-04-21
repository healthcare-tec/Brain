#!/bin/bash
set -e

echo "🧠 Charlie — Cognitive Operating System"
echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
