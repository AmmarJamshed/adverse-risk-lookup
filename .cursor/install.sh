#!/usr/bin/env bash
# ARL Cloud Agent — idempotent environment bootstrap.
# Prepares the full local development stack described in README.md:
# PostgreSQL 16 + pgvector, Redis, the FastAPI backend (+ Celery), and the Vite PWA frontend.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DB_URL="postgresql+psycopg2://arl:arl_secure_password@localhost:5432/arl"

echo "==> [1/7] System packages (PostgreSQL 16 + pgvector, Redis, build tools)"
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -y
sudo apt-get install -y --no-install-recommends \
  postgresql postgresql-contrib postgresql-16-pgvector \
  redis-server build-essential libpq-dev \
  python3-venv python3-pip

echo "==> [2/7] Start PostgreSQL + Redis"
sudo pg_ctlcluster 16 main start || true
for _ in $(seq 1 30); do pg_isready -h localhost -p 5432 >/dev/null 2>&1 && break; sleep 1; done
redis-cli ping >/dev/null 2>&1 || redis-server --daemonize yes --save "" --appendonly no
for _ in $(seq 1 30); do redis-cli ping >/dev/null 2>&1 && break; sleep 1; done

echo "==> [3/7] Provision database role + database + pgvector extension"
sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='arl'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE ROLE arl LOGIN PASSWORD 'arl_secure_password';"
sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='arl'" | grep -q 1 || \
  sudo -u postgres createdb -O arl arl
sudo -u postgres psql -d arl -c "CREATE EXTENSION IF NOT EXISTS vector;" >/dev/null
sudo -u postgres psql -d arl -c "GRANT ALL ON SCHEMA public TO arl;" >/dev/null

echo "==> [4/7] Environment file (.env)"
if [ ! -f .env ]; then
  cp .env.example .env
  JWT="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
  python3 - "$JWT" <<'PY'
import sys, pathlib
jwt = sys.argv[1]
p = pathlib.Path(".env")
t = p.read_text().replace("JWT_SECRET=change-me-to-a-long-random-secret", f"JWT_SECRET={jwt}")
# Blank out placeholder third-party credentials so the app uses its built-in
# offline fallbacks (heuristic analysis, local assistant, hash embeddings)
# instead of making authenticated calls with fake keys. Add real keys to
# enable Groq AI, NewsAPI collection, and Appwrite storage.
for placeholder in (
    "NEWS_API_KEY=your_newsapi_key_here",
    "GROQ_API_KEY=your_groq_api_key_here",
    "APPWRITE_PROJECT_ID=your_appwrite_project_id",
    "APPWRITE_API_KEY=your_appwrite_api_key",
):
    key = placeholder.split("=", 1)[0]
    t = t.replace(placeholder, f"{key}=")
p.write_text(t)
PY
fi

echo "==> [5/7] Python virtualenv + backend dependencies"
[ -d backend/.venv ] || python3 -m venv backend/.venv
# shellcheck disable=SC1091
source backend/.venv/bin/activate
python -m pip install --upgrade pip wheel setuptools
pip install -r backend/requirements.txt

echo "==> [6/7] Database migrations + seed data"
export DATABASE_URL="$DB_URL"
export PYTHONPATH="$REPO_ROOT/backend"
( cd backend && alembic upgrade head && python -m app.seed )

echo "==> [7/7] Frontend dependencies"
( cd frontend && npm ci )

echo "ARL install complete. Login: admin@arl.local / ChangeMe123!"
