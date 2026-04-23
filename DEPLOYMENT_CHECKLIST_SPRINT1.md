# Sprint 1 — AI Assistant Feature: Production Deployment Checklist

## Pre-Deployment (Local Testing)

- [x] AI Conversation Service (`services/ai_conversation_service.py`)
  - [x] Conversation history storage
  - [x] Rate limiting (10/student/day)
  - [x] Quick prompts generation
  - [x] Database schema (migrations/007_ai_features.sql)

- [x] Enhanced AI Service (`services/ai_service.py`)
  - [x] Conversation context injection
  - [x] Error handling with fallbacks
  - [x] Graceful degradation (no API key)

- [x] AI Routes (`routes/ai_routes.py`)
  - [x] Student chat endpoint with rate limiting
  - [x] Quick prompts endpoint
  - [x] Faculty chat endpoint
  - [x] Faculty student summary endpoint

- [x] App Bootstrap (`app.py`)
  - [x] Added `ensure_ai_tables_consistency()` to bootstrap

- [x] Tests (`tests/test_ai_assistant.py`)
  - [x] Conversation history tests
  - [x] Rate limiting tests
  - [x] Quick prompts tests

- [x] Documentation (`docs/AI_ASSISTANT_FEATURE.md`)

## Deployment Steps (To Render)

### Step 1: Set Gemini API Key in Render Dashboard

1. Go to [https://render.com/dashboard](https://render.com/dashboard)
2. Select your "smart-campus-intelligence" service
3. Go to **Environment** tab
4. Add/Edit: `GEMINI_API_KEY`
   - Value: Get from [https://aistudio.google.com](https://aistudio.google.com)
   - Click "Get API Key" → Create new project → Copy key
5. Save changes (auto-deploys)

**Verify**: 
```bash
curl https://your-render-url/health/ready
# Should show "healthy"
```

### Step 2: Database Migrations Run Automatically
- `app.py` bootstrap now includes `ensure_ai_tables_consistency()`
- Tables created on app startup:
  - `ai_conversations` (conversation history)
  - `ai_rate_limits` (rate limiting)

**Verify in psql:**
```sql
\d ai_conversations
\d ai_rate_limits
```

### Step 3: Test Endpoints

**Test 1: Quick Prompts (no auth needed)**
```bash
curl -H "Authorization: Bearer <student-jwt>" \
  https://your-render-url/ai/quick-prompts
# Should return 200 with prompt list
```

**Test 2: Student Chat (requires student token)**
```bash
curl -X POST \
  -H "Authorization: Bearer <student-jwt>" \
  -H "Content-Type: application/json" \
  -d '{"message":"Why is my readiness score dropping?"}' \
  https://your-render-url/ai/chat/student
# Should return 200 with AI response
```

**Test 3: Rate Limiting (make 11 requests in quick succession)**
```bash
for i in {1..11}; do
  curl -X POST \
    -H "Authorization: Bearer <student-jwt>" \
    -H "Content-Type: application/json" \
    -d "{\"message\":\"Test $i\"}" \
    https://your-render-url/ai/chat/student
done
# Request 11 should return 429 (Too Many Requests)
```

**Test 4: Faculty Summary (requires faculty token)**
```bash
curl -H "Authorization: Bearer <faculty-jwt>" \
  https://your-render-url/ai/faculty/student-summary/42
# Should return 200 with AI-generated summary
```

### Step 4: Monitoring & Validation

Monitor these logs after deployment:

**Success Indicators:**
- Log: `ensure_ai_tables_consistency()` called during bootstrap
- HTTP 200 responses for `/ai/chat/student` with AI response text
- Rate limit headers in response

**Error Indicators:**
- `Gemini init failed: ...` — Missing or invalid API key
- `Could not fetch student context` — Dashboard data fetch issue
- `ThreadedConnectionPool` errors — Database connection issue

**Check Logs:**
```bash
render logs <service-id> --follow
```

### Step 5: Database Verification

SSH into Render Postgres:
```bash
psql $DATABASE_URL

-- Verify tables exist
\d ai_conversations
\d ai_rate_limits

-- Check sample data (after first user chat)
SELECT student_id, role, created_at FROM ai_conversations LIMIT 5;
SELECT student_id, request_count, reset_at FROM ai_rate_limits LIMIT 5;
```

---

## Feature Rollout Plan

### Phase 1 (Day 1): Silent Deploy
- Deploy code to production
- Verify health check: `GET /health/ready` → 200
- Verify no errors in logs

### Phase 2 (Day 1-2): Faculty Testing
- 5-10 faculty test `/ai/faculty/student-summary/<student_id>`
- Verify AI summaries are reasonable
- Collect feedback on response quality

### Phase 3 (Day 3): Limited Student Launch (10 students)
- Enable `/ai/quick-prompts` in student dashboard
- Monitor:
  - Response times (should be <2s)
  - Gemini token usage (should be <10k/day for 10 students)
  - Rate limit triggers

### Phase 4 (Day 4+): Full Launch
- Enable for all students
- Monitor:
  - Daily active users (DAU)
  - Tokens consumed (vs free tier limit: 1M/day)
  - User engagement (repeat users asking follow-up questions)

---

## Rollback Plan

If AI feature causes issues:

```bash
# Option 1: Disable AI endpoints (no code change needed)
# Set in app: return 503 for /ai/* routes

# Option 2: Remove API key
# Unset GEMINI_API_KEY from Render dashboard
# App returns graceful fallback message

# Option 3: Roll back deployment
# In Render dashboard: Deploy → select previous working deployment
```

---

## Post-Deployment Metrics

Track in first week:

| Metric | Target | How to Measure |
|--------|--------|---|
| Endpoint latency | <2s | Render logs or APM |
| Gemini token usage | <500k/day | Google Cloud Console |
| Student chat requests/day | TBD | Query `ai_conversations` table |
| Rate limit triggers/day | <5% of requests | Query `ai_rate_limits` |
| Error rate | <1% | Parse error responses from logs |

**Query to check usage:**
```sql
-- Last 24 hours of messages
SELECT COUNT(*), role FROM ai_conversations 
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY role;

-- Rate limit resets (past 24h)
SELECT COUNT(*) FROM ai_rate_limits 
WHERE updated_at > NOW() - INTERVAL '24 hours';
```

---

## Issues & Fixes

### Issue: API Key rejected
**Fix**: 
1. Verify key is valid: test at [aistudio.google.com](https://aistudio.google.com)
2. Check for extra spaces: `GEMINI_API_KEY` should not have leading/trailing spaces
3. Recreate key: old keys may have been revoked

### Issue: Responses take >5s
**Fix**:
1. Check Gemini API status: [status.cloud.google.com](https://status.cloud.google.com)
2. Reduce context size: Limit conversation history to 5 messages instead of 10
3. Switch model: Try `gemini-1.5-flash` instead of `gemini-2.0-flash`

### Issue: Rate limiter not resetting
**Fix**: Manually reset for testing:
```sql
DELETE FROM ai_rate_limits WHERE student_id = 1;
```

### Issue: Students see "AI assistant needs Gemini API key"
**Fix**: 
- `GEMINI_API_KEY` is not set or empty
- Set in Render dashboard, then restart deployment

---

## Success Criteria (Definition of Done)

✅ **Render Deployment Complete When:**
1. App boots without errors (`GET /health/ready` → 200)
2. AI tables exist in database (verified via psql)
3. Faculty can call `/ai/faculty/student-summary/<id>` → 200
4. Student rate limit tested: 10 requests allowed, 11th returns 429
5. Conversation history persists across calls
6. No errors in Render logs
7. Gemini API key validation works (graceful fallback if missing)

✅ **Feature Launch Complete When:**
1. Student dashboard shows "AI Chat" widget
2. Faculty dashboard shows "Get AI Summary" button
3. 5+ students use feature in first 48 hours
4. No critical errors reported
5. Gemini token usage <1% of free tier (1M/day)

---

## Next Step

Once this deploys successfully, immediately start **Sprint 2: Company Matcher** (the most emotionally resonant feature).

---

**Deployed by**: [Your Name]  
**Date**: [Deployment Date]  
**Environment**: Render (Production)  
**Status**: 🟢 Ready for Launch
