# Architecture

## Summary

Smart Campus Intelligence System is a Flask + PostgreSQL application structured as a production-style SaaS backend with server-rendered pages and JSON APIs. It is intentionally monolithic for portfolio clarity, but the code is split into routes, services, migrations, and core infrastructure modules so interviewers can see clean boundaries.

## System Flow

```text
User Browser
  -> Flask route / Blueprint
  -> Auth middleware + tenant context
  -> Service layer
  -> PostgreSQL via ThreadedConnectionPool
  -> JSON response or Jinja template
```

## Multi-Tenancy

The app uses a shared-schema tenancy model:

- `institutions` stores each campus/tenant.
- Core records use `institution_id`.
- Public auth flows may resolve tenant from `X-Institution-Code`, `institution_code`, query/body, or subdomain.
- Protected APIs use the institution embedded in the JWT as the source of truth.
- Tenant admins operate only within their institution.
- Super admins can view global data and create institutions.

This design is simpler than database-per-tenant, easier to run on Render's free/low-cost PostgreSQL tier, and realistic for a small-college SaaS pilot.

## Security

Security controls include:

- JWT auth with `jti` claim and database-backed blacklist.
- Bcrypt password hashing.
- Login timing-attack mitigation.
- Rate limits on auth-sensitive endpoints.
- HTTP security headers including CSP, HSTS on HTTPS, frame protection, and content-type protection.
- Secure cookie settings for production.
- Tenant-scoped uniqueness constraints for users and students.
- Audit logging for sensitive admin actions.

## Data Layer

The app uses PostgreSQL with:

- Ordered SQL migrations.
- Automatic migration execution during startup.
- `ThreadedConnectionPool` for production WSGI workers.
- Readiness checks that verify database availability.
- Tenant-aware indexes for common lookup paths.

SQLite is intentionally not supported for production because Render disks are ephemeral and SQLite write concurrency is a poor fit for multi-instance SaaS deployment.

## AI Design

AI features are optional and degrade safely:

- If `GEMINI_API_KEY` is absent, the assistant returns a helpful fallback.
- AI routes are plan-gated with `PLAN_FEATURES`.
- Student AI context is built from dashboard metrics, alerts, and conversation history.
- Faculty AI context is built from class analytics and intervention summaries.

The project treats AI as an assistive layer, not a source of truth.

## Operational Design

Production-oriented capabilities:

- `/health/live` for liveness.
- `/health/ready` for database-backed readiness.
- `/health/startup` for bootstrap metadata.
- Structured logging and request IDs.
- CSV exports/imports for admin operations.
- Async report-job simulation for long-running work.
- Render Blueprint for repeatable deployment.

## Tradeoffs

- Monolith over microservices: faster to understand, test, and deploy for a portfolio project.
- Shared-schema tenancy over database-per-tenant: lower operational cost and simpler Render deployment.
- In-memory async job registry over Celery/Redis: demonstrates background-job design without adding infrastructure before it is necessary.
- Jinja/Vanilla JS over SPA: keeps product scope focused on backend, data, and production engineering.

## Next Production Steps

- SSO/SAML/OIDC for institution login.
- Persistent job queue with Redis/Celery.
- Object storage for uploaded resources.
- Full audit coverage across every sensitive mutation.
- Monitoring dashboard with error rates, latency, and DB pool metrics.
- SIS/LMS integrations and CSV templates for real campus onboarding.
