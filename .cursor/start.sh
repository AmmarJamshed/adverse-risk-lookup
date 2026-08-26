#!/usr/bin/env bash
# ARL Cloud Agent — per-boot service startup.
# Brings up PostgreSQL and Redis (no systemd in the VM) and ensures the schema
# is present. Idempotent: safe to run repeatedly and on every boot.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DB_URL="postgresql+psycopg2://arl:arl_secure_password@localhost:5432/arl"

echo "==> Starting PostgreSQL"
sudo pg_ctlcluster 16 main start || true
for _ in $(seq 1 30); do pg_isready -h localhost -p 5432 >/dev/null 2>&1 && break; sleep 1; done

echo "==> Starting Redis"
redis-cli ping >/dev/null 2>&1 || redis-server --daemonize yes --save "" --appendonly no
for _ in $(seq 1 30); do redis-cli ping >/dev/null 2>&1 && break; sleep 1; done

# Ensure the schema exists (no-op once migrated; guards a fresh volume).
if [ -d backend/.venv ]; then
  # shellcheck disable=SC1091
  source backend/.venv/bin/activate
  export DATABASE_URL="$DB_URL"
  export PYTHONPATH="$REPO_ROOT/backend"
  ( cd backend && alembic upgrade head >/dev/null 2>&1 || true )
fi

echo "ARL services ready — PostgreSQL:5432, Redis:6379"
