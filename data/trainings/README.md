# Trainings data pack

Sanitized training listings for:

Saudi Arabia, Bahrain, Qatar, Oman, Germany, France, Czech Republic,
Netherlands, Canada, Japan, Malaysia, Singapore.

## Files
- `trainings.json` — machine-readable feed used by the app API
- `TRAININGS.md` — human-readable mirror with register links

## Refresh
```bash
python scripts/scrape_trainings.py
python scripts/scrape_trainings.py --country "Singapore"
# Always safe fallback if Eventbrite rate-limits the scraper:
python scripts/merge_seed_trainings.py
```

Verified registration URLs for sparse markets live in `harvest_seed.json` and are
merged into every weekly scrape.

## GitHub Actions (per country, staggered)

Each country has its own workflow so Eventbrite is not hit all at once.
Schedules are Mondays, 20 minutes apart (UTC):

| Workflow | UTC |
|---|---|
| `trainings-saudi-arabia.yml` | 06:00 |
| `trainings-bahrain.yml` | 06:20 |
| `trainings-qatar.yml` | 06:40 |
| `trainings-oman.yml` | 07:00 |
| `trainings-germany.yml` | 07:20 |
| `trainings-france.yml` | 07:40 |
| `trainings-czech-republic.yml` | 08:00 |
| `trainings-netherlands.yml` | 08:20 |
| `trainings-canada.yml` | 08:40 |
| `trainings-japan.yml` | 09:00 |
| `trainings-malaysia.yml` | 09:20 |
| `trainings-singapore.yml` | 09:40 |

Shared job logic: `trainings-scrape-reusable.yml`  
Full sequential run (manual): `weekly-trainings.yml`

Register buttons open the Eventbrite event page directly (tracking params stripped).
