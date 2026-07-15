# Public Docker Deploy (no local Docker Desktop)

The API image builds **in the cloud** via Fly.io remote builders or Render.

## Option A — Fly.io (recommended)

1. Open [Fly billing](https://fly.io/dashboard/muhammad-ammar-jamshed/billing) and add a payment method (required by Fly to create apps).
2. Tell the agent “Fly billing done” — or run:

```powershell
cd D:\Projects\adverse-risk-lookup\backend
$env:Path = "$env:USERPROFILE\.fly\bin;" + $env:Path
$env:JWT_SECRET = (Select-String -Path ..\.env -Pattern '^JWT_SECRET=(.+)$').Matches.Groups[1].Value
$env:GROQ_API_KEY = (Select-String -Path ..\.env -Pattern '^GROQ_API_KEY=(.+)$').Matches.Groups[1].Value
$env:NEWS_API_KEY = (Select-String -Path ..\.env -Pattern '^NEWS_API_KEY=(.+)$').Matches.Groups[1].Value

flyctl apps create arl-adverse-risk-lookup --org personal
flyctl volumes create arl_data --app arl-adverse-risk-lookup --region iad --size 1 -y
flyctl secrets set JWT_SECRET=$env:JWT_SECRET GROQ_API_KEY=$env:GROQ_API_KEY NEWS_API_KEY=$env:NEWS_API_KEY CORS_ORIGINS="https://arl-adverse-risk-lookup.netlify.app,https://arl-adverse-risk-lookup.fly.dev" DATABASE_URL="sqlite:////data/arl.db" APP_ENV=production APP_DEBUG=false USE_FAISS_FALLBACK=true --app arl-adverse-risk-lookup
flyctl deploy --remote-only --ha=false --app arl-adverse-risk-lookup
```

API URL becomes: `https://arl-adverse-risk-lookup.fly.dev`

## Option B — Render

1. Sign in at https://dashboard.render.com with GitHub
2. **New → Blueprint** → select repo `AmmarJamshed/adverse-risk-lookup`
3. Set `GROQ_API_KEY` and `NEWS_API_KEY` when prompted

## Frontend

Already live: https://arl-adverse-risk-lookup.netlify.app  
After API is up, rebuild Netlify with `VITE_API_URL=https://YOUR-API-HOST/api`
