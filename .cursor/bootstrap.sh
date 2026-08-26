#!/usr/bin/env bash
# ARL Cloud Agent — idempotent per-repo bootstrap.
#
# Ensures the repository-local artifacts that the app needs at runtime exist:
# the .env file, the Python virtualenv (+ backend deps), the frontend
# node_modules, the database schema, and seed data.
#
# Heavy steps (pip install, npm ci) run ONLY when their artifact is missing, so:
#   - warm boots and repeated installs stay fast (nothing to do), and
#   - a pod booted from a prebuilt environment build self-heals — that boot
#     performs a fresh git checkout which wipes the gitignored .venv /
#     node_modules / .env from the working tree, so they are rebuilt here
#     using the pip/npm caches preserved in the snapshot.
#
# Called by both .cursor/install.sh (baseline setup) and .cursor/start.sh
# (per-boot readiness).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DB_URL="postgresql+psycopg2://arl:arl_secure_password@localhost:5432/arl"

echo "==> bootstrap: environment file (.env)"
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

echo "==> bootstrap: Python virtualenv + backend dependencies"
if [ ! -x backend/.venv/bin/python ]; then
  python3 -m venv backend/.venv
  backend/.venv/bin/python -m pip install --upgrade pip wheel setuptools
  backend/.venv/bin/pip install -r backend/requirements.txt
fi
# shellcheck disable=SC1091
source backend/.venv/bin/activate

echo "==> bootstrap: frontend dependencies"
if [ ! -d frontend/node_modules ]; then
  ( cd frontend && npm ci )
fi

echo "==> bootstrap: database migrations + seed data"
export DATABASE_URL="$DB_URL"
export PYTHONPATH="$REPO_ROOT/backend"
( cd backend && alembic upgrade head && python -m app.seed )

echo "==> bootstrap: complete"
