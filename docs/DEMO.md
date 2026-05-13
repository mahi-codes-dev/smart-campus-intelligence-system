# Demo And Deployment Guide

## Render Demo Setup

1. Push the repository to GitHub.
2. Open Render and create a new Blueprint from the repo.
3. Render will use `render.yaml` to create:
   - Python web service.
   - Managed PostgreSQL database.
   - `/health/ready` health check.
4. Set optional secrets:
   - `GEMINI_API_KEY` for AI assistant.
   - `SMTP_USERNAME` and `SMTP_PASSWORD` for OTP email.
5. After first deploy, run the seed script from a Render shell or locally against the Render `DATABASE_URL`.

```bash
python scripts/seed_data.py
```

## Demo Accounts

Use these account patterns for a portfolio demo after seeding:

| Role | Email | Password |
| --- | --- | --- |
| Faculty | `faculty@smartcampus.edu` | `password123` |
| Seeded students | generated as `firstname.lastname.index@example.edu` | `password123` |

Recommended extra manual accounts:

| Role | Purpose |
| --- | --- |
| Super Admin | Show institution management and global audit view |
| Institution Admin | Show tenant-scoped admin dashboard |
| Student | Show placement readiness, goals, company matching, AI |
| Faculty | Show intervention workflow and class analytics |

## Interview Demo Script

1. Start on `/health/ready` to show production readiness and runtime metadata.
2. Log in as admin and show tenant context, users, exports, audit logs, and report jobs.
3. Log in as faculty and show class summary, at-risk students, classroom marks, and interventions.
4. Log in as student and show readiness score, goals, company matching, peer learning, and AI fallback/advice.
5. Explain how tenant isolation is enforced from JWT claims across protected APIs.

## What To Say In Interviews

This project is not positioned as a full university ERP. It is a focused student-success and placement-readiness SaaS prototype. The engineering focus is production readiness: tenant isolation, secure auth, PostgreSQL migrations, Render deployment, health checks, audit logs, CSV workflows, and tests.

## Screenshots To Add

Add screenshots to `docs/screenshots/` once the app is deployed:

- `login.png`
- `student-dashboard.png`
- `faculty-summary.png`
- `admin-dashboard.png`
- `audit-logs.png`
- `health-ready.png`

Then link them from the README.
