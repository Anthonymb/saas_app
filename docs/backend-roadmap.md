# Backend Roadmap

This document is the working backend execution plan for the project. It captures the phased SaaS roadmap, delivery priorities, and the ticket backlog we will use to guide daily implementation work.

## Principles

- Stabilize the current foundation before adding broad new surface area.
- Introduce tenancy before deep billing or team features.
- Keep request handlers thin and push business rules into services/domain logic.
- Prefer explicit transactions, typed errors, and strong test coverage.
- Design for async/background processing before scaling outbound workflows.

## Phased Plan

### Phase 1: Stabilize The Foundation

1. Remove risky defaults and harden config.
2. Fix transaction and error handling.
3. Clean schema duplication.
4. Add real tests.

### Phase 2: Introduce SaaS Tenancy

1. Add `Organization`, `Membership`, and roles.
2. Move ownership from user-only boundaries to organization/workspace boundaries.
3. Add tenant-aware authorization.
4. Update migrations and seed data.

### Phase 3: Build Core SaaS Modules

1. Add contacts module.
2. Add campaigns module.
3. Add messages lifecycle and delivery state.
4. Add billing foundations and entitlement checks.

### Phase 4: Improve Scalability

1. Introduce background workers and queues.
2. Add pagination, filtering, and search across core endpoints.
3. Add indexes based on real query paths.
4. Separate integrations from business logic.

### Phase 5: Harden For Production

1. Add refresh-token rotation and revocation.
2. Add rate limiting and audit logging.
3. Add structured logging, metrics, health/readiness, and tracing.
4. Add CI and deployment readiness checks.

## 12-Week Execution Plan

### Week 1: Foundation Audit And Cleanup

1. Clean up duplicated schemas and shared types.
2. Standardize imports, naming, and module boundaries.
3. Remove risky defaults like fallback secrets.
4. Define coding conventions for routes, services, models, and schemas.

### Week 2: Testing Baseline

1. Set up real `pytest` coverage for auth and user flows.
2. Add fixtures for app, DB session, and test users.
3. Cover register, login, refresh, change password, and profile update/delete.
4. Add migration or startup smoke tests.

### Week 3: Transaction And Error Handling

1. Remove request-level auto-commit behavior.
2. Move commit/rollback responsibility into service or unit-of-work boundaries.
3. Add typed application errors instead of broad `Exception` handling.
4. Improve API error responses and internal logging.

### Week 4: Observability And App Hardening

1. Replace `print` statements with structured logging.
2. Add request IDs and correlation IDs.
3. Improve `/health` and `/health/db`.
4. Add environment-aware settings for local/dev/prod.

### Week 5: Tenant Model Design

1. Introduce `Organization` and `Membership`.
2. Define roles such as owner, admin, and member.
3. Decide which models become organization-owned.
4. Write migrations for tenancy.

### Week 6: Tenant Authorization

1. Add current organization context to auth/session flow.
2. Scope queries by tenant.
3. Prevent cross-tenant access in services and endpoints.
4. Add tests for tenant isolation.

### Week 7: Contacts Module

1. Build contacts CRUD endpoints.
2. Add pagination, filtering, and search.
3. Add contact status management and suppression behavior.
4. Add tests for validation and tenant scoping.

### Week 8: Campaigns Module

1. Build campaign CRUD and draft lifecycle.
2. Add scheduling fields and validation.
3. Connect campaigns to contacts/messages cleanly.
4. Add campaign listing and detail stats.

### Week 9: Messaging And Delivery Model

1. Improve message state transitions.
2. Add provider message identifiers and event history.
3. Model delivery, bounce, open, and click events.
4. Prepare for async sending architecture.

### Week 10: Background Jobs And Queue

1. Introduce Redis plus a worker system.
2. Move sending, retries, scheduled jobs, and webhook processing out of request handlers.
3. Add retry policies and dead-letter handling.
4. Add worker health and operational visibility.

### Week 11: Billing And Entitlements

1. Add plans, subscriptions, and entitlement checks.
2. Build payment webhook ingestion flow.
3. Connect billing state to feature access.
4. Add audit-safe payment event handling.

### Week 12: Security And Production Readiness

1. Add refresh-token rotation and revocation.
2. Add rate limiting and audit logging.
3. Finalize CI for tests, migrations, and linting.
4. Write deployment checklist and runbook.

## Ticket Backlog

| ID | Priority | Title | Description | Outcome | Suggested Sprint |
|---|---|---|---|---|---|
| BE-001 | Must-have | Consolidate auth/token schemas | Remove duplicated token models and keep one source of truth for auth-related schemas. | Cleaner schema layer, less drift risk. | Sprint 1 |
| BE-002 | Must-have | Harden environment config | Remove insecure fallback secrets, validate required env vars, and separate dev/prod settings behavior. | Safer startup and production readiness. | Sprint 1 |
| BE-003 | Must-have | Add auth and user test baseline | Create tests for register, login, refresh, change password, get/update/delete profile. | Regression safety for current functionality. | Sprint 1 |
| BE-004 | Must-have | Refactor DB transaction handling | Stop auto-committing at request dependency level and move commit control into service/application layer. | Safer, more explicit write behavior. | Sprint 1 |
| BE-005 | Must-have | Improve exception handling | Replace broad exception swallowing with typed app errors and structured API responses. | Better observability and safer failures. | Sprint 1 |
| BE-006 | Must-have | Add structured logging | Replace `print` statements with proper logging, request IDs, and environment-aware log formatting. | Easier debugging and operations. | Sprint 1 |
| BE-007 | Must-have | Introduce Organization model | Add `Organization` entity as the top-level SaaS tenant boundary. | Correct SaaS ownership model. | Sprint 2 |
| BE-008 | Must-have | Introduce Membership and roles | Add `Membership` model with roles like owner/admin/member. | Multi-user tenant support. | Sprint 2 |
| BE-009 | Must-have | Add tenant-scoped authorization | Ensure all protected data queries are scoped to the active organization. | Tenant isolation and security. | Sprint 2 |
| BE-010 | Must-have | Build contacts module | Add contacts CRUD, list, search, pagination, and tenant ownership. | First real SaaS data module. | Sprint 3 |
| BE-011 | Must-have | Build campaigns module | Add campaign CRUD, draft lifecycle, schedule fields, and ownership rules. | Campaign management foundation. | Sprint 3 |
| BE-012 | Must-have | Build messages lifecycle | Support message creation, status transitions, provider IDs, and event tracking. | Reliable delivery model. | Sprint 3 |
| BE-013 | Must-have | Add background job infrastructure | Introduce Redis/worker queue for async campaign sending and retries. | Scalable async processing. | Sprint 4 |
| BE-014 | Must-have | Implement refresh token revocation | Add token rotation, revocation/blocklist, and real logout behavior. | Stronger auth security. | Sprint 4 |
| BE-015 | Must-have | Add CI pipeline | Run tests, migration checks, and linting automatically. | Safer iteration and deploy confidence. | Sprint 4 |
| BE-016 | Should-have | Improve health/readiness endpoints | Split liveness, readiness, and DB checks with cleaner responses. | Better deployment and monitoring behavior. | Sprint 5 |
| BE-017 | Should-have | Add audit logging | Record sensitive actions like password changes, role changes, billing events, and destructive operations. | Better compliance and debugging. | Sprint 5 |
| BE-018 | Should-have | Add contact tagging and segmentation | Support tags, filters, and dynamic contact groups. | Better campaign targeting. | Sprint 5 |
| BE-019 | Should-have | Add campaign analytics | Expose sent, delivered, opened, clicked, bounced metrics. | Product value for messaging workflows. | Sprint 5 |
| BE-020 | Should-have | Add webhook ingestion framework | Add provider webhook endpoints with signature verification and idempotency. | Safer third-party event processing. | Sprint 5 |
| BE-021 | Should-have | Add billing plans and subscriptions | Model plans, subscriptions, and feature entitlements. | Monetization foundation. | Sprint 6 |
| BE-022 | Should-have | Add rate limiting | Protect auth and sensitive endpoints from abuse. | Better security and resilience. | Sprint 6 |
| BE-023 | Should-have | Add repository/query layer | Separate database query concerns from services as modules grow. | Cleaner architecture at scale. | Sprint 6 |
| BE-024 | Later | Add invitation flow | Invite users into organizations by email with role assignment. | Better team onboarding. | Later |
| BE-025 | Later | Add email verification | Verify user emails during sign-up or invite acceptance. | Better account trust and deliverability. | Later |
| BE-026 | Later | Add forgot/reset password flow | Tokenized password recovery with expiry and audit events. | Complete auth lifecycle. | Later |
| BE-027 | Later | Add feature flags and entitlements | Gate premium capabilities by plan or tenant settings. | Flexible SaaS packaging. | Later |
| BE-028 | Later | Add metrics and tracing | Export app metrics and distributed traces. | Better performance and ops visibility. | Later |
| BE-029 | Later | Add admin backoffice endpoints | Internal tools for tenant support, billing review, and moderation. | Better operational support. | Later |
| BE-030 | Later | Add data export/import jobs | Support CSV import/export for contacts and reports. | Better customer onboarding and retention. | Later |

## Delivery Order

1. Sprint 1: `BE-001` to `BE-006`
2. Sprint 2: `BE-007` to `BE-009`
3. Sprint 3: `BE-010` to `BE-012`
4. Sprint 4: `BE-013` to `BE-015`
5. Sprint 5+: `BE-016` onward

## Working Agreement

- This roadmap is the default reference for backend prioritization.
- Daily implementation tasks should map back to one of the backlog items when possible.
- If product needs change, update this document rather than letting the execution plan drift informally.
