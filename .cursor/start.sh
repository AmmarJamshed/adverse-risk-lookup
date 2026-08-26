#!/usr/bin/env bash
# ARL Cloud Agent — per-boot service startup.
# Brings up PostgreSQL and Redis (no systemd in the VM), then runs the shared
# idempotent bootstrap so repository-local artifacts (.env, venv, node_modules,
# schema, seed) are present even when this pod booted from a prebuilt build
# whose fresh git checkout wiped those gitignored paths. Idempotent and fast on
# warm boots (heavy steps are skipped when their artifact already exists).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> Starting PostgreSQL"
sudo pg_ctlcluster 16 main start || true
for _ in $(seq 1 30); do pg_isready -h localhost -p 5432 >/dev/null 2>&1 && break; sleep 1; done

echo "==> Starting Redis"
redis-cli ping >/dev/null 2>&1 || redis-server --daemonize yes --save "" --appendonly no
for _ in $(seq 1 30); do redis-cli ping >/dev/null 2>&1 && break; sleep 1; done

echo "==> Ensuring repository artifacts (.env, venv, node_modules, schema, seed)"
bash "$REPO_ROOT/.cursor/bootstrap.sh"

echo "ARL services ready — PostgreSQL:5432, Redis:6379"
