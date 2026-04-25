# Sprint 2 Company Matcher — Testing & Deployment Guide

## ✅ What's Complete

### Core Implementation
- ✅ Database migration (`migrations/008_placement_companies.sql`)
- ✅ Company matching service (`services/company_matching_service.py`)
  - 10+ default companies (TCS, Infosys, Wipro, Microsoft, etc.)
  - Match score calculation (marks 40%, attendance 30%, mock 20%, skills 10%)
  - Gap analysis (shows student exactly what's needed)
  - Eligibility tiers (eligible now 90%+, close 75-89%, aspirational 0-74%)

- ✅ HTTP Routes (`routes/company_routes.py`)
  - `GET /student/company-matches` — Student sees all matches
  - `POST /admin/companies/seed` — Admin seeds default companies (idempotent)
  - `GET /admin/companies` — Admin lists all companies
  - `POST /admin/companies` — Admin adds new companies
  - `GET /student/company-matches/insights` — AI-powered company insights

- ✅ Tests (12 passing)
  - Company seeding (idempotency verified)
  - Match score calculations (perfect match, with gaps, partial skills)
  - Score weighting algorithm
  - Eligibility categorization
  - Integration tests

### Blueprint Registration
- ✅ `app.py` imports `company_bp`
- ✅ `app.py` registers `company_bp`
- ✅ `app.py` calls `ensure_companies_table_consistency()` in bootstrap

---

## 🧪 Local Testing

### Option 1: Run All Unit Tests (Recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Run company matching tests
pytest tests/test_company_matching.py -v

# Or run all tests
pytest tests/ -v
```

**Expected Result**: All 12 company matching tests pass ✅

---

### Option 2: Manual API Testing with cURL

#### 1. Generate a Student JWT Token

```bash
# Run Python script to generate token
python3 -c "
import jwt
from config import settings
payload = {'user_id': 1, 'role': 'Student', 'email': 'student@test.com'}
token = jwt.encode(payload, settings.jwt_secret, algorithm='HS256')
print(token)
"
# Save the token output
TOKEN=<paste-token-here>
```

#### 2. Start the Flask App Locally

```bash
# Terminal 1: Start Flask dev server
export FLASK_ENV=development
python app.py
# Or with gunicorn for production-like testing:
gunicorn --workers 1 --bind 0.0.0.0:5000 wsgi:app
```

#### 3. Test Student Endpoint

```bash
# Get all company matches for authenticated student
curl -X GET http://localhost:5000/student/company-matches \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Expected Response (200 OK):
{
  "student_name": "Student Name",
  "eligible_now": [
    {
      "id": 1,
      "name": "TCS (Tata Consultancy Services)",
      "package": "3.5 LPA",
      "sector": "IT Consulting",
      "match_score": 94.2
    }
  ],
  "eligible_with_improvement": [
    {
      "id": 2,
      "name": "Infosys",
      "package": "4.5 LPA",
      "sector": "IT Services",
      "match_score": 78.5,
      "gap": "Need 8.2 more points in marks (61.8% → 70%)"
    }
  ],
  "stretch_targets": [...],
  "summary": {
    "ready_to_apply": 1,
    "close_to_ready": 5,
    "aspirational": 4
  }
}
```

#### 4. Admin: Seed Default Companies

```bash
# Generate admin token
ADMIN_TOKEN=<admin-token>

# Seed companies (idempotent — safe to call multiple times)
curl -X POST http://localhost:5000/admin/companies/seed \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json"

# Expected Response (201 Created):
{
  "message": "Default companies seeded successfully",
  "count": 10,
  "companies": [
    {"id": 1, "name": "TCS (Tata Consultancy Services)", "package": 3.5, ...}
  ]
}
```

#### 5. Admin: List All Companies

```bash
curl -X GET http://localhost:5000/admin/companies \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json"

# Expected Response (200 OK):
{
  "total": 10,
  "companies": [
    {
      "id": 1,
      "name": "TCS (Tata Consultancy Services)",
      "package": 3.5,
      "sector": "IT Consulting",
      "min_marks": 65,
      "required_skills": ["Java", "Python", "SQL"]
    },
    ...
  ]
}
```

#### 6. Admin: Add a Custom Company

```bash
curl -X POST http://localhost:5000/admin/companies \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Amazon India",
    "min_marks_percentage": 75,
    "min_attendance": 85,
    "min_mock_score": 80,
    "package_lpa": 7.0,
    "sector": "Technology",
    "required_skills": ["Java", "System Design", "AWS"]
  }'

# Expected Response (201 Created):
{
  "message": "Company added successfully",
  "company_id": 11
}
```

#### 7. Get AI Insights (Optional — requires Gemini API key)

```bash
curl -X GET "http://localhost:5000/student/company-matches/insights?company_name=Infosys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Response with API key:
{
  "insights": "Based on your profile, Infosys is within reach. Your marks (61.8%) are slightly below their requirement (70%). ...",
  "eligible_now": 1,
  "eligible_with_improvement": 5
}

# Response without API key (graceful fallback):
{
  "insights": "AI insights require Gemini API key. Check your dashboard for company matches instead."
}
```

---

## 🚀 Deployment to Render

### Step 1: Verify Database Migrations

The database migration runs automatically during app bootstrap:

```python
# app.py bootstrap includes:
run_migrations()  # Runs all .sql migrations including 008_placement_companies.sql
ensure_companies_table_consistency()  # Ensures tables exist
```

### Step 2: Deploy to Render

```bash
# Push code to GitHub
git add -A
git commit -m "Sprint 2: Company Matcher feature complete"
git push origin main

# Render auto-deploys on push (if webhook is configured)
# Or manually deploy:
# 1. Go to https://render.com/dashboard
# 2. Select your service
# 3. Click "Deploy" (or it auto-deploys on push)
```

### Step 3: Verify Deployment

```bash
# Check app health
curl https://<your-render-url>/health/ready
# Expected: 200 with "healthy"

# Seed companies on Render (one-time setup)
curl -X POST https://<your-render-url>/admin/companies/seed \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

### Step 4: Monitor in Production

**Track these metrics:**

| Metric | Target | How to Track |
|--------|--------|-------------|
| Student company matches | All students see results | Manual: test with student token |
| Admin seeding | Idempotent | Call `/admin/companies/seed` twice, should succeed both times |
| Error rate | <1% | Check Render logs |
| Response time | <500ms | Use browser dev tools or `time curl` command |

**Logs on Render:**

```bash
# View app logs
# 1. Go to https://render.com/dashboard
# 2. Select service
# 3. Click "Logs" tab
# 4. Search for "company" or "placement"
```

---

## 📊 Feature Highlights

### For Students
- **"You are 8 points away from Infosys"** — Emotional hook for daily engagement
- Three-tier categorization:
  - 🟢 **Eligible Now** (90%+): Apply immediately
  - 🟡 **Close to Ready** (75-89%): Here's what's needed
  - ⚪ **Aspirational** (0-74%): Stretch targets with skill gaps

### For Faculty/Admin
- Seed 10 default companies (TCS, Infosys, Wipro, Cognizant, Accenture, HCL, Tech Mahindra, IBM, Microsoft, Google)
- Add custom companies with requirements
- Manage placement criteria

### Matching Algorithm
```
Score = (marks_match × 0.4) + (attendance_match × 0.3) + 
        (mock_match × 0.2) + (skills_match × 0.1)
```

Each metric: `student_value / required_value × 100`, capped at 100.

---

## 🔧 Troubleshooting

### Issue: "Company matches endpoint returns 404"

**Solution**: Ensure blueprint is registered in `app.py`
```python
from routes.company_routes import company_bp
app.register_blueprint(company_bp)
```

### Issue: "No companies are showing up"

**Solution**: Seed companies via admin endpoint
```bash
curl -X POST http://localhost:5000/admin/companies/seed \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Issue: "Student scores are 0 or missing"

**Solution**: This endpoint depends on the student having readiness data. Ensure:
1. Student has attendance records
2. Student has mock test scores
3. Student has skills in `student_skills` table

### Issue: "Match scores seem incorrect"

**Debugging**: Print student metrics to logs
```python
# In company_matching_service.py
student_metrics = {
    "marks": readiness.get("marks", 0),
    "attendance": readiness.get("attendance", 0),
    "mock_score": readiness.get("mock_score", 0),
    "skills": student_skills,
}
logger.info(f"Student {student_id} metrics: {student_metrics}")
```

---

## ✅ Pre-Deployment Checklist

- [ ] All 12 company matching tests pass locally
- [ ] Database migration runs without errors
- [ ] Admin can seed companies (POST `/admin/companies/seed`)
- [ ] Student can fetch matches (GET `/student/company-matches`)
- [ ] Gap messages are accurate
- [ ] Admin can add custom companies
- [ ] Error handling works (graceful fallbacks for missing data)
- [ ] Response times acceptable (<500ms)
- [ ] No SQL injection vulnerabilities (parameterized queries used)

---

## 📝 Next Sprint Ideas (Sprint 3+)

1. **Company Preferences**: Students mark companies as "interested"
2. **Application Tracking**: Track which companies student applied to
3. **Peer Comparison**: "8 students from your batch got Infosys"
4. **Skill Recommendations**: "Learn Python to unlock Infosys"
5. **Email Alerts**: "You're now eligible for 2 new companies!"
6. **Analytics Dashboard**: "Most popular companies", "Easiest to qualify for"
