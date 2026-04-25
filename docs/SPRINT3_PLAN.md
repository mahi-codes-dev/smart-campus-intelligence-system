# 🎓 SPRINT 3: Peer Learning Feed

## Executive Summary

**Peer Learning Feed** enables students to see achievements and learning activities of their peers, fostering community and motivation through transparent, non-competitive engagement. Students see:
- Who got placed at which companies
- Peer skill recommendations and shares
- Study group formations
- Achievement badges

This feature drives daily engagement and creates healthy peer support culture.

---

## 🎯 What We'll Build

### Core Features

#### 1. **Peer Placement Achievements**
Students see (anonymized + consented):
- "8 students from CS-A got Infosys" (placement tier)
- When they got placed (timeline)
- What their peer profile looked like
- Motivational message: "You're on track!"

#### 2. **Peer Skill Marketplace**
- Browse skills learned by peers
- "5 students just finished 'Docker' training"
- "Learn Python - 12 peers recommend it"
- Link to resources shared by peers

#### 3. **Study Groups & Learning Circles**
- Form groups with 2-4 peers
- Goal-based: "AWS Certification Sept 30"
- Track group progress together
- Share resources within group

#### 4. **Feed Preferences & Privacy**
- Opt-in/out of visibility
- Toggle which data shows (placements, skills, etc.)
- Anonymous by default (use anonymized ID)
- Peers see: achievement, not full name initially

---

## 📊 Database Schema

### New Tables

**peer_achievements**
```sql
id SERIAL PRIMARY KEY
student_id INTEGER NOT NULL FOREIGN KEY (students)
achievement_type VARCHAR (placement|skill|badge|goal)
achievement_data JSONB {
  "company": "Infosys",
  "date": "2024-03-15",
  "score": 78.5,
  "sector": "IT",
  "offer_package": 4.5
}
is_anonymous BOOLEAN (default true)
consent_given BOOLEAN (default false)
created_at TIMESTAMP
```

**peer_skills**
```sql
id SERIAL PRIMARY KEY
student_id INTEGER FOREIGN KEY (students)
skill_name VARCHAR (Python, AWS, Docker, etc.)
proficiency_level INT (1-5)
date_learned TIMESTAMP
shared BOOLEAN (default false)
resource_link VARCHAR
recommendation_count INT (default 0)
created_at TIMESTAMP
```

**study_groups**
```sql
id SERIAL PRIMARY KEY
name VARCHAR
description TEXT
goal VARCHAR (e.g., "AWS Certification by Sept 30")
created_by INTEGER FOREIGN KEY (students)
target_date DATE
status VARCHAR (active|completed|paused)
max_members INT (default 4)
created_at TIMESTAMP
```

**study_group_members**
```sql
id SERIAL PRIMARY KEY
study_group_id INTEGER FOREIGN KEY (study_groups)
student_id INTEGER FOREIGN KEY (students)
joined_at TIMESTAMP
role VARCHAR (creator|member)
contribution_score INT (default 0)
```

**peer_feed_preferences**
```sql
id SERIAL PRIMARY KEY
student_id INTEGER UNIQUE FOREIGN KEY (students)
show_placements BOOLEAN (default true)
show_skills BOOLEAN (default true)
show_study_groups BOOLEAN (default true)
anonymous_mode BOOLEAN (default true)
email_on_peer_achievement BOOLEAN (default false)
created_at TIMESTAMP
updated_at TIMESTAMP
```

---

## 🛠 Implementation Tasks

### Phase 1: Database & Schema (Iteration 1)
- [ ] Create migration `009_peer_learning.sql`
- [ ] Ensure schema consistency function
- [ ] Index on (student_id, created_at) for feed queries

### Phase 2: Service Layer (Iteration 2)
- [ ] `services/peer_learning_service.py`
  - `ensure_peer_tables_consistency()` — Schema bootstrap
  - `record_peer_achievement()` — Log placements, skills, badges
  - `get_peer_feed_for_student()` — Personalized feed (50 items, chronological)
  - `get_peer_achievements_summary()` — Dashboard stats
  - `toggle_peer_preferences()` — Privacy controls
  - Study group functions

### Phase 3: HTTP Routes (Iteration 3)
- [ ] `routes/peer_learning_routes.py`
  - `GET /student/peer-feed` — Main feed (paginated)
  - `GET /student/peer-achievements` — Filter by type (placement, skill, badge)
  - `GET /student/peer-skills` — Popular skills trending
  - `POST /student/peer-preferences` — Update privacy settings
  - `GET /student/peer-preferences` — Get current settings
  - Study group endpoints (create, join, leave, list)

### Phase 4: Testing (Iteration 4)
- [ ] `tests/test_peer_learning.py`
  - Peer achievement creation
  - Feed filtering and pagination
  - Privacy/anonymity enforcement
  - Study group operations
  - Preference updates

### Phase 5: Integration & Deployment (Iteration 5)
- [ ] Register blueprint in `app.py`
- [ ] Bootstrap call in startup
- [ ] Documentation & API examples
- [ ] Deploy to Render

---

## 🏗 Architecture Flow

```
POST /student/record-achievement
  ↓
peer_learning_service.record_peer_achievement()
  ↓
INSERT into peer_achievements (with privacy checks)
  ↓
Trigger: Update peer_feed_preferences (notify subscribers)
  ↓
GET /student/peer-feed
  ↓
peer_learning_service.get_peer_feed_for_student()
  ↓
Query peer_achievements + ANONYMIZE based on preferences
  ↓
Return: [ {achievement, student_profile, consent}, ... ]
```

---

## 🔐 Privacy & Safety

✅ **Anonymity by Default**
- Students see "Student from CS-A" not full names
- Only share if both parties consented
- Can opt out at any time

✅ **No Bullying**
- Achievements never ranked (no leaderboards)
- No comparative scores shown
- Focus on learning path, not competition
- Can report inappropriate achievements

✅ **Data Minimization**
- Only share what student opted into
- 30-day auto-anonymization option
- GDPR compliant (right to forget)

---

## 📈 Success Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| Daily Active Users on Feed | >60% of students | Peer engagement driver |
| Avg Feed Page Time | >2 min | Rich content keeps attention |
| Study Group Formation Rate | 1 per 5 students | Community building |
| Skill Share Rate | 20% of learners | Knowledge sharing |
| Opt-in Rate | >70% | Privacy-first approach |

---

## 📋 Files to Create/Modify

### New Files
- `migrations/009_peer_learning.sql` (schema)
- `services/peer_learning_service.py` (business logic)
- `routes/peer_learning_routes.py` (HTTP endpoints)
- `tests/test_peer_learning.py` (comprehensive tests)
- `SPRINT3_TESTING_GUIDE.md` (deployment & testing)
- `SPRINT3_COMPLETE.md` (summary)

### Modified Files
- `app.py` — Add blueprint registration + bootstrap
- `requirements.txt` — Any new dependencies (none expected)

---

## ⏱ Estimated Timeline

- Phase 1 (DB Schema): 30 min
- Phase 2 (Service Logic): 90 min
- Phase 3 (Routes): 60 min
- Phase 4 (Tests): 90 min
- Phase 5 (Integration): 30 min
- **Total: ~5 hours** (can be spread across 1-2 days)

---

## 🚀 Next Steps After Sprint 3

1. **Skill Gap Recommendations** — "Learn Python to unlock Infosys"
2. **Email Alerts** — "You're now eligible for 2 new companies!"
3. **Admin Analytics** — "Most popular companies", "Easiest to qualify"
4. **Application Tracking** — Track which companies student applied to
5. **Peer Comparison** — Safe benchmarking without competition

Ready to start Phase 1? 🎯
