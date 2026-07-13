#!/bin/sh
set -e
# Persist SQLite on Fly volume when DATABASE_URL is not set
if [ -z "$DATABASE_URL" ]; then
  export DATABASE_URL="sqlite:////data/arl.db"
fi
mkdir -p /data /app/uploads /app/logs /app/data/faiss_index
echo "ARL: preparing database..."
python -m app.seed || true
echo "ARL: starting API on :${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
