# Adverse Risk Lookup (ARL)

**Tagline:** Transforming Global Banking News into Actionable Risk Intelligence.

Enterprise-grade AI platform for banks, Islamic banks, insurers, fintechs, central banks, and regulators. Continuously collects global adverse media, analyzes it with Groq LLMs, embeds content for semantic risk-register matching (pgvector / FAISS), and surfaces explainable operational risk intelligence.

Deploy the **frontend as a PWA on Netlify**; run the **API + workers** via Docker (or any Linux/Windows host).

---

## Architecture

| Module | Technology |
|--------|------------|
| Frontend PWA | React, TypeScript, Tailwind, React Query, Chart.js, Vite PWA |
| API | FastAPI, SQLAlchemy, JWT/RBAC |
| Workers | Celery + Redis (news every 15 min) |
| Database | PostgreSQL + **pgvector** |
| AI | Groq (analysis, translation, assistant) |
| Embeddings | BAAI BGE / sentence-transformers (+ FAISS fallback) |
| Optional files | Appwrite Cloud storage |
| Containers | Docker Compose |

### Design notes

- **Appwrite** (`APPWRITE_ENDPOINT` / `APPWRITE_PROJECT_ID`) is configured for optional file storage. It is **not** a PostgreSQL replacement — ARL’s system of record is Postgres + pgvector for SQLAlchemy and semantic search. Set `DATABASE_URL` to your Postgres instance (Docker Compose provides one by default).
- Secrets live in `.env` only. `.env.example` uses placeholders — never commit real keys.

---

## Quick start (Docker)

```bash
cd adverse-risk-lookup
cp .env.example .env
# Edit .env — set NEWS_API_KEY, GROQ_API_KEY, JWT_SECRET, DATABASE_URL, REDIS_URL

docker compose up --build
```

Services:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API docs | http://localhost:8000/api/docs |
| Health | http://localhost:8000/api/health |
| Postgres | localhost:5432 |
| Redis | localhost:6379 |

**Demo login:** `admin@arl.local` / `ChangeMe123!`

---

## Local development

### Backend

```bash
# Start Postgres + Redis (or use docker compose up db redis -d)
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
cd ..
# Ensure .env exists at repo root
cd backend
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

Workers (separate terminals):

```bash
celery -A app.workers.celery_app worker --loglevel=info
celery -A app.workers.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests

```bash
cd backend
pytest -q
```

---

## Netlify PWA deploy

1. Push the repo to GitHub/GitLab.
2. In Netlify: **Add site → Import** → set base directory to `frontend`.
3. Build command: `npm run build` · Publish: `dist`.
4. Set `VITE_API_URL=/api`.
5. Edit `frontend/netlify.toml` redirect `/api/*` to your hosted FastAPI URL (Render, Fly.io, Railway, Azure, etc.).
6. Install as PWA from the browser (manifest + service worker via `vite-plugin-pwa`).

---

## Environment variables

See [`.env.example`](.env.example). Critical keys:

```text
NEWS_API_KEY=
GROQ_API_KEY=
DATABASE_URL=postgresql+psycopg2://arl:arl_secure_password@localhost:5432/arl
JWT_SECRET=<long random string>
REDIS_URL=redis://localhost:6379/0
APPWRITE_ENDPOINT=https://fra.cloud.appwrite.io/v1
APPWRITE_PROJECT_ID=
```

Generate JWT secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## Core capabilities

- **News collection** — NewsAPI + unlimited RSS feeds (regulators, CERT, central banks, etc.)
- **Multilingual** — detect language; store original + English; UI language toggle (en/es/ar/ur/hi+)
- **AI relevance** — banking / GRC domains via Groq (not keyword-only)
- **Duplicate clustering** — embedding similarity → master + linked duplicates
- **Risk register upload** — CSV/Excel column-mapping wizard
- **Semantic matching** — embeddings + explainable reasoning, controls, KRIs, departments
- **Dashboard** — severity, categories, countries, sources, languages, critical alerts
- **Alerts** — conditional subscriptions + in-app notifications
- **Reports** — PDF & Excel management packs
- **AI Assistant** — grounded Q&A over recent intelligence
- **Admin** — users, RBAC, feeds, job logs, prompt templates, audit logs
- **Scheduler** — Celery beat every 15 minutes with retries & job logs

---

## Folder structure

```text
adverse-risk-lookup/
├── backend/app/          # FastAPI modules, services, workers, prompts
├── frontend/             # React PWA (Netlify)
├── samples/              # Risk register + RSS samples
├── scripts/init-db.sql   # pgvector extension
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Sample assets

- [`samples/sample_risk_register.csv`](samples/sample_risk_register.csv)
- [`samples/sample_rss_feeds.json`](samples/sample_rss_feeds.json)

---

## Security

JWT auth · role-based access · rate limiting · audit trails · validated uploads · no hardcoded secrets · OWASP-oriented defaults.

---

## License

Proprietary / organizational use — configure for your institution and jurisdiction.
