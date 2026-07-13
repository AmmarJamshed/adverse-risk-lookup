# Installation Guide — Adverse Risk Lookup (ARL)

## Prerequisites

- Docker Desktop (recommended) **or** Python 3.11+, Node 20+, PostgreSQL 16 + pgvector, Redis 7
- Groq API key
- NewsAPI key

## 1. Configure environment

```bash
cp .env.example .env
```

Set at minimum:

- `JWT_SECRET` — long random string
- `DATABASE_URL` — Postgres (`postgresql+psycopg2://arl:arl_secure_password@localhost:5432/arl`)
- `REDIS_URL` — `redis://localhost:6379/0`
- `NEWS_API_KEY`
- `GROQ_API_KEY`
- `APPWRITE_ENDPOINT` / `APPWRITE_PROJECT_ID` — optional file storage only

> Appwrite Cloud is **not** a SQL database. ARL requires PostgreSQL for ORM + pgvector.

## 2. Start with Docker Compose

```bash
docker compose up --build
```

Open http://localhost:5173 — login `admin@arl.local` / `ChangeMe123!`

## 3. Netlify PWA

1. Connect repository
2. Base directory: `frontend`
3. Build: `npm run build` · Publish: `dist`
4. Point `/api/*` redirects in `frontend/netlify.toml` to your FastAPI host
5. Install to home screen — PWA manifest & service worker are included

## 4. Seed & samples

Seed runs automatically in Docker. Manually:

```bash
cd backend && python -m app.seed
```

Upload `samples/sample_risk_register.csv` via **Risk Register → Upload Wizard**.

## 5. First intelligence cycle

1. **News Sources → Collect from NewsAPI** or **Fetch now** on an RSS feed
2. Ensure Celery worker is running to process `pending` articles
3. Review **Dashboard** and **Adverse Media**
4. Open an article for explainable risk matches

## Troubleshooting

| Issue | Fix |
|-------|-----|
| JWT errors | Ensure `JWT_SECRET` is set and identical across API/workers |
| pgvector errors | Use `pgvector/pgvector:pg16` image; run `scripts/init-db.sql` |
| Slow first start | sentence-transformers downloads embedding weights once |
| CORS | Add your Netlify URL to `CORS_ORIGINS` |
