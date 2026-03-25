# SaaS Backend

This repository contains the backend for a multi-tenant SaaS application built with FastAPI, SQLAlchemy, PostgreSQL, and Alembic.

## What is Included

- JWT auth with token rotation and revocation
- Organization and membership tenancy
- Contacts, campaigns, messages, payments, jobs, and audit logs
- Database-backed background job processing for campaign sends and payment webhooks
- Health, readiness, worker, and audit visibility endpoints

## Quick Start

1. Create and activate the virtual environment.
2. Install dependencies from `requirements.txt`.
3. Configure your environment variables.
4. Run migrations.
5. Start the API.

Example commands on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\alembic.exe upgrade head
uvicorn app.main:app --reload
```

## Test and Verify

Run the automated test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run the local smoke test:

```powershell
.\scripts\backend-smoke-test.ps1
```

Open the API docs in development:

- `http://127.0.0.1:8000/docs`

## Useful Docs

- [Backend Roadmap](docs/backend-roadmap.md)
- [Polish Pass](docs/polish-pass.md)
- [Backend Walkthrough](docs/backend-walkthrough.md)
- [Deployment Checklist](docs/deployment-checklist.md)
