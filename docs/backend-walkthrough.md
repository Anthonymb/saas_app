# Backend Walkthrough

This document is the quick orientation guide for the SaaS backend before frontend integration begins.

## Stack

- FastAPI for the HTTP API
- SQLAlchemy async ORM for persistence
- PostgreSQL as the primary database
- Alembic for schema migrations
- JWT auth with persistent token session tracking
- A DB-backed job queue for async campaign and webhook work

## Core Flows

### Auth and Session Flow

- `POST /api/v1/auth/register` creates a user, a personal organization, and an owner membership.
- `POST /api/v1/auth/login` issues access and refresh tokens.
- Tokens include the active organization context.
- Refresh rotation revokes the old refresh token and creates a new session pair.
- Logout revokes the active access token server-side.

### Tenancy Model

- `Organization` is the top-level tenant boundary.
- `Membership` maps users to organizations with roles.
- Contacts, campaigns, payments, jobs, and audit logs are organization-scoped.
- Messages inherit tenancy through their parent campaign/contact validation path.

### Campaign and Messaging Flow

- Contacts are created per organization.
- Campaigns are created per organization.
- Messages are generated under campaigns using organization-owned contacts.
- Campaign responses include analytics derived from message state counts.
- Campaign sends are queued as jobs instead of running inline.

### Queue and Worker Flow

- `POST /api/v1/campaigns/{campaign_id}/queue-send` enqueues a campaign send job.
- `POST /api/v1/webhooks/payments/{provider}` enqueues payment webhook processing.
- `POST /api/v1/jobs/run-once` processes one queued job for local testing.
- Health endpoints expose worker and queue visibility:
  - `/api/v1/health/liveness`
  - `/api/v1/health/db`
  - `/api/v1/health/readiness`
  - `/api/v1/health/worker`

## API Surface

### Auth

- `/api/v1/auth/register`
- `/api/v1/auth/login`
- `/api/v1/auth/refresh`
- `/api/v1/auth/context`
- `/api/v1/auth/me`
- `/api/v1/auth/change-password`
- `/api/v1/auth/logout`

### Core SaaS Resources

- `/api/v1/contacts`
- `/api/v1/campaigns`
- `/api/v1/campaigns/{campaign_id}/messages`
- `/api/v1/payments`
- `/api/v1/jobs`
- `/api/v1/audit-logs`

## Operational Notes

- Request IDs are attached to responses and logs via `X-Request-ID`.
- Audit logs are written for auth-sensitive actions, core resource CRUD, and queue enqueue events.
- Rate limiting is currently in-memory and suitable for local/dev use, not distributed production scale.
- The queue is currently database-backed. It is intentionally simple and can later be replaced by Redis/Celery/RQ/Arq if throughput demands it.

## Before Frontend Work

- Run the automated tests.
- Run the smoke test script in `scripts/backend-smoke-test.ps1`.
- Verify PostgreSQL and migrations are up to date.
- Use `/docs` to inspect the current OpenAPI contract.
