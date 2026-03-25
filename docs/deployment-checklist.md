# Deployment Checklist

## Environment

- Set `SECRET_KEY` to a strong random value of at least 32 characters.
- Set PostgreSQL connection variables for the target environment.
- Set `APP_ENV` and `DEBUG` appropriately for production.
- Confirm `ALLOWED_ORIGINS` matches the deployed frontend domains.

## Database

- Run `alembic upgrade head`.
- Verify new tables exist: `organizations`, `memberships`, `jobs`, `token_sessions`, `audit_logs`.
- Confirm at least one test user can log in and access `/api/v1/auth/context`.

## App Validation

- Start the API successfully.
- Verify `/api/v1/health` and `/api/v1/health/db`.
- Verify login, refresh, logout, contacts, campaigns, messages, and payments endpoints.
- Verify `POST /api/v1/campaigns/{campaign_id}/queue-send` queues a job.
- Verify `POST /api/v1/jobs/run-once` processes a queued job.

## Security

- Confirm token refresh rotates tokens.
- Confirm logout revokes the active access token.
- Confirm rate limiting returns `429` after repeated abuse on sensitive endpoints.
- Confirm audit logs are written for auth-sensitive actions.

## Operations

- Run the campaign worker if async jobs should be processed continuously:
  `python -m app.workers.campaign_worker`
- Check `/api/v1/jobs/health` for backlog/failure visibility.
