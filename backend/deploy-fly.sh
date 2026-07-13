#!/usr/bin/env bash
# Deploy ARL API to Fly.io using remote builders (no Docker Desktop required)
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.fly/bin:$PATH"

: "${JWT_SECRET:?Set JWT_SECRET}"
: "${GROQ_API_KEY:?Set GROQ_API_KEY}"
: "${NEWS_API_KEY:?Set NEWS_API_KEY}"

flyctl apps create arl-adverse-risk-lookup --org personal 2>/dev/null || true
flyctl volumes create arl_data --region iad --size 1 -y 2>/dev/null || true

flyctl secrets set \
  JWT_SECRET="$JWT_SECRET" \
  GROQ_API_KEY="$GROQ_API_KEY" \
  NEWS_API_KEY="$NEWS_API_KEY" \
  CORS_ORIGINS="https://arl-adverse-risk-lookup.netlify.app,https://arl-adverse-risk-lookup.fly.dev" \
  DATABASE_URL="sqlite:////data/arl.db" \
  APP_ENV=production \
  APP_DEBUG=false \
  USE_FAISS_FALLBACK=true

flyctl deploy --remote-only --ha=false
echo "API: https://arl-adverse-risk-lookup.fly.dev"
