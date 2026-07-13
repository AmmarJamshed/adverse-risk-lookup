#!/bin/sh
set -e
if [ -z "$DATABASE_URL" ]; then
  export DATABASE_URL="sqlite:////data/arl.db"
fi
mkdir -p /data /app/uploads /app/logs /app/data/faiss_index
echo "ARL: preparing database..."
python -m app.seed || true
PORT_VALUE="${PORT:-7860}"
echo "ARL: starting API on :${PORT_VALUE}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT_VALUE}"
