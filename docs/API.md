# ARL REST API Overview

Base URL: `/api/v1`  
Interactive docs: `/api/docs`

## Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/login` | JWT login |
| POST | `/auth/register` | Register (first user = super_admin) |
| GET | `/auth/me` | Current user |

Header: `Authorization: Bearer <token>`

## Articles & search

| Method | Path | Description |
|--------|------|-------------|
| GET | `/articles` | Filterable list (q, country, bank, language, severity, …) |
| GET | `/articles/{id}` | Detail + explainable risk matches |
| POST | `/articles/{id}/reprocess` | Re-run AI pipeline |

## Risk register

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/risks` | List / create |
| POST | `/risks/upload/preview` | Column mapping preview |
| POST | `/risks/upload/import` | Import with mapping JSON form field |

## Feeds & collection

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/feeds` | List / add RSS |
| POST | `/feeds/{id}/fetch` | Fetch one feed |
| POST | `/feeds/collect-newsapi` | NewsAPI ingest |

## Dashboard / alerts / reports / admin

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard/stats` | Widget aggregates |
| GET | `/dashboard/heatmap` | Country × category |
| CRUD | `/alerts/subscriptions` | Alert rules |
| GET | `/notifications` | Inbox |
| GET | `/reports/pdf` | PDF download |
| GET | `/reports/excel` | Excel download |
| POST | `/assistant` | AI assistant |
| GET | `/emerging-risks` | Emerging themes |
| GET | `/admin/users` | User admin |
| GET | `/admin/audit-logs` | Audit trail |
| GET | `/admin/jobs` | Celery job logs |
