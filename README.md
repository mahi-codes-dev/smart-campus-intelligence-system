# 🎓 Smart Campus Intelligence System

A full-stack campus management platform built with **Flask + PostgreSQL**, featuring role-based access control, AI-powered academic advising, placement readiness prediction, and real-time notifications.

> **Built for MAANG-level resume impact** — demonstrates backend architecture, security practices, AI integration, and production deployment on Render.

---

## ✨ Feature Highlights

| Area | What's included |
|------|----------------|
| **Auth** | JWT (cookie + Bearer), bcrypt hashing, OTP password reset, token blacklist, rate limiting |
| **Roles** | Admin · Faculty · Student — fully separated dashboards and APIs |
| **Student** | Readiness score, placement prediction, attendance, marks, skills, goals, peer learning, wellbeing |
| **Faculty** | Class analytics, at-risk alerts, intervention tracking, notice board, resource uploads |
| **Admin** | User management, department management, system health |
| **AI** | Gemini-powered personal advisor for students and class insights for faculty |
| **Security** | CSP headers, HSTS, X-Frame-Options, no user enumeration, timing-attack-safe login |
| **Ops** | Migration runner, `/health/live` + `/health/ready` endpoints, structured logging |

---

## 🚀 Deploy on Render (one-click)

1. Fork / push this repo to GitHub.
2. Go to [render.com](https://render.com) → **New Blueprint**.
3. Connect your GitHub repo — Render picks up `render.yaml` automatically.
4. It provisions a **free PostgreSQL** database and a **free web service**.
5. After deploy, set the optional secrets in the Render dashboard:
   - `GEMINI_API_KEY` — for AI assistant (free key at [aistudio.google.com](https://aistudio.google.com/app/apikey))
   - `SMTP_USERNAME` / `SMTP_PASSWORD` — for OTP email (Gmail App Password)

> The first deploy runs all SQL migrations automatically. No manual DB setup needed.

---

## 🛠 Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL 14+

### Setup

```bash
# 1. Clone
git clone https://github.com/your-username/smart-campus-intelligence-system.git
cd smart-campus-intelligence-system

# 2. Virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — fill in DB credentials and JWT_SECRET / SECRET_KEY

# 5. Create the database
createdb smart_campus_db       # or use pgAdmin / psql

# 6. Run (migrations run automatically on startup)
python app.py
```

Open [http://localhost:5000](http://localhost:5000)

### Seed demo data

```bash
python scripts/seed_data.py
```

---

## 🏗 Architecture

```
smart-campus-intelligence-system/
├── app.py                  # Flask app factory, error handlers, root routes
├── wsgi.py                 # Gunicorn entry point
├── config.py               # Typed settings from environment variables
├── database.py             # Connection pool (psycopg2 ThreadedConnectionPool)
├── auth/
│   ├── auth_middleware.py  # JWT token_required / role_required decorators
│   └── auth_routes.py      # /auth/login, /auth/register, /auth/logout, OTP reset
├── core/
│   ├── logging_config.py   # Structured logging
│   ├── rate_limiter.py     # Sliding-window per-IP rate limiter
│   └── security_headers.py # CSP, HSTS, X-Frame-Options, etc.
├── routes/                 # One Blueprint per feature domain
├── services/               # Business logic layer (no Flask imports)
├── migrations/             # Ordered SQL migrations (auto-applied on startup)
├── templates/              # Jinja2 HTML templates
│   └── errors/             # 400, 403, 404, 500 error pages
├── static/                 # CSS, JS, PWA manifest + service worker
├── utils/
│   ├── validators.py       # Input sanitisation + validation helpers
│   └── response.py         # Standardised JSON response helpers
└── render.yaml             # Render Blueprint (IaC)
```

---

## 🔐 Security Notes

- Passwords hashed with **bcrypt** (cost factor 12)
- Login uses **constant-time comparison** to prevent timing-based user enumeration
- All logins and registrations are **rate-limited**
- JWT tokens carry a **`jti`** claim; logout adds it to a **blacklist table**
- HTTP responses include **Content-Security-Policy**, **X-Frame-Options**, **HSTS** (on HTTPS), and other OWASP-recommended headers
- Passwords capped at 128 chars to prevent DoS via bcrypt's O(n) cost

---

## 📡 Key API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/login` | — | Login, returns JWT |
| POST | `/auth/register` | — | Register new user |
| POST | `/auth/logout` | ✓ | Revoke token |
| POST | `/auth/forgot-password` | — | Request OTP |
| POST | `/auth/reset-password` | — | Reset via OTP |
| GET  | `/health/live` | — | Liveness probe |
| GET  | `/health/ready` | — | Readiness probe (checks DB) |
| POST | `/ai/chat/student` | Student | AI academic advisor |
| POST | `/ai/chat/faculty` | Faculty | AI class insights |

---

## 🧪 Health Checks

```bash
curl http://localhost:5000/health/live   # {"status":"alive"}
curl http://localhost:5000/health/ready  # {"status":"healthy","database":"connected"}
```

---

## 📜 License

MIT — see `LICENSE` for details.
