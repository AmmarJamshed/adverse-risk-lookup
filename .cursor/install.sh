#!/usr/bin/env bash
# ARL Cloud Agent — baseline environment setup.
# Installs system dependencies and provisions the database, then runs the
# shared idempotent per-repo bootstrap. Prepares the full local development
# stack described in README.md: PostgreSQL 16 + pgvector, Redis, the FastAPI
# backend (+ Celery), and the Vite PWA frontend.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> [1/4] System packages (PostgreSQL 16 + pgvector, Redis, build tools)"
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -y
sudo apt-get install -y --no-install-recommends \
  postgresql postgresql-contrib postgresql-16-pgvector \
  redis-server build-essential libpq-dev \
  python3-venv python3-pip

echo "==> [2/4] Start PostgreSQL + Redis"
sudo pg_ctlcluster 16 main start || true
for _ in $(seq 1 30); do pg_isready -h localhost -p 5432 >/dev/null 2>&1 && break; sleep 1; done
redis-cli ping >/dev/null 2>&1 || redis-server --daemonize yes --save "" --appendonly no
for _ in $(seq 1 30); do redis-cli ping >/dev/null 2>&1 && break; sleep 1; done

echo "==> [3/4] Provision database role + database + pgvector extension"
sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='arl'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE ROLE arl LOGIN PASSWORD 'arl_secure_password';"
sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='arl'" | grep -q 1 || \
  sudo -u postgres createdb -O arl arl
sudo -u postgres psql -d arl -c "CREATE EXTENSION IF NOT EXISTS vector;" >/dev/null
sudo -u postgres psql -d arl -c "GRANT ALL ON SCHEMA public TO arl;" >/dev/null

echo "==> [4/4] Repository bootstrap (.env, venv, deps, migrations, seed)"
bash "$REPO_ROOT/.cursor/bootstrap.sh"

echo "ARL install complete. Login: admin@arl.local / ChangeMe123!"
