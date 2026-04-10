# Smart Campus Intelligence System

A full-stack student performance analytics platform built with Flask, PostgreSQL, and vanilla HTML/CSS/JavaScript.

The system helps institutions monitor student readiness using a weighted scoring model based on:

- Attendance
- Academic marks
- Skills
- Mock test performance

It includes role-based workflows for Admin, Faculty, and Student users, along with dashboard pages and protected JSON APIs.

## Features

- JWT-based authentication
- Role-based access control for Admin, Faculty, and Student users
- Student dashboard with readiness score, risk level, alerts, insights, and placement outlook
- Faculty dashboard for attendance, marks, mock tests, student filtering, and detail views
- Admin dashboard for user management, subject management, and department-level analytics
- Department and subject management
- Skill assignment and self-added student skills
- Placement prediction based on readiness score
- Top-student and low-performer analytics

## Tech Stack

- Backend: Flask
- Database: PostgreSQL
- Authentication: JWT + bcrypt
- Frontend: HTML, CSS, JavaScript
- Database driver: psycopg2

## Project Structure

smart-campus-intelligence-system/
│
├── auth/           # Authentication logic
├── routes/         # API endpoints
├── services/       # Business logic
├── templates/      # HTML pages
├── static/         # JS & CSS
├── utils/          # Helpers
│
├── app.py
├── database.py
├── requirements.txt
├── api-test.http
└── .env.example
## How It Works

The platform calculates a readiness score from four academic indicators:

- Attendance: 30%
- Marks: 40%
- Skills: 20%
- Mock Tests: 10%

Current readiness formula:

```text
final_score =
  (attendance * 0.3) +
  (marks * 0.4) +
  (skills_score * 0.2) +
  (mock_score * 0.1)
```

Status bands used by the scoring service:

- `>= 80`: Placement Ready
- `>= 60`: Moderate
- `< 60`: Needs Improvement

The student dashboard also derives:

- Risk level
- Placement outlook
- Alerts
- Insights
- Strongest and weakest metric
- Subject-wise performance summary

## User Roles

### Admin

- View overall system analytics
- View and delete users
- Add and delete subjects
- Monitor top students by department
- Monitor low-performing students

### Faculty

- View students and filter by department/search
- Save attendance percentage
- Save marks and exam type
- Save mock test scores
- View student-level performance details

### Student

- Register and log in
- View personal dashboard
- Track progress and readiness
- View profile and subject performance
- Add personal skills

## Prerequisites

- Python 3.10+ recommended
- PostgreSQL
- A database created for the project

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd smart-campus-intelligence-system
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root.

Example:

```env
DB_HOST=localhost
DB_NAME=smart_campus
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432

JWT_SECRET=replace_with_a_strong_secret
JWT_ALGORITHM=HS256
JWT_EXP_HOURS=24
```

## Database Setup

The application now bootstraps its own schema on startup through SQL migrations plus the active consistency checks. That includes:

- `roles`
- `users`
- `departments`
- `students`
- `subjects`
- `attendance`
- `marks`
- `skills`
- `student_skills`
- `mock_tests`
- `student_goals`
- `goal_milestones`
- `student_badges`
- `notifications`
- `notification_preferences`
- `theme_preferences`
- `student_interventions`

### Tables managed by the application

On startup, the project ensures the following tables and relationships exist:

- `departments`
- `students`
- `subjects`
- `attendance`
- `marks`
- `skills`
- `student_skills`
- `mock_tests`

## Running the Project

Start the Flask development server:

```bash
python app.py
```

Default local URL:

```text
http://127.0.0.1:5000
```

Production entrypoint:

```bash
gunicorn wsgi:application
```

Frontend pages:

- `/` -> Login page
- `/register` -> Registration page
- `/student-dashboard`
- `/student-progress`
- `/student-skills`
- `/student-profile`
- `/faculty-dashboard`
- `/admin-dashboard`

## Main API Endpoints

### Authentication

- `GET /auth/roles`
- `POST /auth/register`
- `POST /auth/login`

### Student

- `GET /students` -> Admin only
- `GET /student/dashboard` -> Student only
- `GET /student/attendance` -> Student only
- `GET /student/skills` -> Student only
- `POST /student/skills` -> Student only
- `GET /student/skills/<student_id>` -> Student/Faculty/Admin access depending on role rules
- `GET /readiness/<student_id>`
- `GET /predict/<student_id>`
- `GET /mock-tests/<student_id>`
- `GET /top-students`

### Faculty

- `GET /faculty/dashboard`
- `GET /faculty/summary`
- `GET /faculty/student/<student_id>`
- `POST /faculty/attendance`
- `POST /marks`
- `PUT /marks`
- `POST /mock-tests`
- `PUT /mock-tests`
- `POST /faculty/student-skills`

### Admin

- `GET /admin/stats`
- `GET /admin/users`
- `DELETE /admin/user/<user_id>`
- `POST /admin/subject`
- `GET /admin/subjects`
- `DELETE /admin/subject/<subject_id>`

### Subject and Legacy Student APIs

- `POST /subjects`
- `GET /subjects`
- `GET /create-table`
- `POST /add-student`
- `PUT /update-student/<id>`
- `DELETE /delete-student/<id>`

## Example Request Flow

### 1. Register a user

```http
POST /auth/register
Content-Type: application/json

{
  "name": "Mahesh",
  "email": "mahesh@test.com",
  "password": "123456",
  "role_id": 1
}
```

### 2. Log in

```http
POST /auth/login
Content-Type: application/json

{
  "email": "mahesh@test.com",
  "password": "123456"
}
```

Use the returned JWT in:

```http
Authorization: Bearer <token>
```

### 3. Create a subject

```http
POST /subjects
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "Data Structures",
  "code": "DS101",
  "department": "CSE"
}
```

### 4. Save marks

```http
PUT /marks
Content-Type: application/json
Authorization: Bearer <faculty-token>

{
  "student_id": 1,
  "subject_id": 1,
  "marks": 84,
  "exam_type": "Midterm"
}
```

## Manual API Testing

The repository includes an `api-test.http` file for quick local API testing in editors that support HTTP request files.

## Health Check

Use the health endpoints to verify runtime status:

```text
GET /health
GET /health/ready
GET /health/live
```

Expected response:

```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Development Notes

- JWT auth is accepted through the `Authorization` header and an HttpOnly auth cookie.
- The frontend is server-rendered with Flask templates and enhanced with vanilla JavaScript.
- Chart rendering is powered by Chart.js from a CDN.
- Database connections are pooled through `ThreadedConnectionPool`.
- Login and registration endpoints are rate-limited in-process.

## Known Gaps / Future Improvements

- Add automated tests
- Move auth token storage away from `localStorage`
- Add API documentation with request/response schemas

## Troubleshooting

### `JWT_SECRET is not configured`

Make sure `.env` contains:

```env
JWT_SECRET=your_secret
JWT_ALGORITHM=HS256
JWT_EXP_HOURS=24
```

### Startup bootstrap fails

Check `/health/ready` for the bootstrap error message and confirm:

- PostgreSQL is reachable from the app
- the configured database user can create or alter tables
- required secrets such as `JWT_SECRET` and `SECRET_KEY` are present

### Database connection errors

Check:

- PostgreSQL is running
- Database name is correct
- Username and password are correct
- Port is correct
- `.env` exists in the project root

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
