from database import get_db_connection


def _fetch_students_with_department():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            s.id,
            COALESCE(NULLIF(s.name, ''), u.name) AS name,
            COALESCE(NULLIF(s.email, ''), u.email) AS email,
            COALESCE(NULLIF(s.department, ''), 'Not Assigned') AS department
        FROM students s
        LEFT JOIN users u ON s.user_id = u.id
        ORDER BY s.id ASC
        """
    )
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def calculate_readiness(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            COUNT(*) FILTER (WHERE status = 'Present') * 100.0 / NULLIF(COUNT(*), 0)
        FROM attendance
        WHERE student_id = %s
        """,
        (student_id,),
    )
    attendance = float(cur.fetchone()[0] or 0)

    cur.execute(
        """
        SELECT AVG(marks)
        FROM marks
        WHERE student_id = %s
        """,
        (student_id,),
    )
    marks = float(cur.fetchone()[0] or 0)

    if attendance < 60 or marks < 50:
        risk_status = "At Risk"
    else:
        risk_status = "Safe"

    cur.execute(
        """
        SELECT COUNT(*)
        FROM student_skills
        WHERE student_id = %s
        """,
        (student_id,),
    )
    skill_count = cur.fetchone()[0] or 0
    skills_score = min(skill_count * 10, 100)

    cur.execute(
        """
        SELECT AVG(score)
        FROM mock_tests
        WHERE student_id = %s
        """,
        (student_id,),
    )
    mock_score = float(cur.fetchone()[0] or 0)

    final_score = (
        0.3 * attendance +
        0.4 * marks +
        0.2 * skills_score +
        0.1 * mock_score
    )

    if final_score >= 80:
        status = "Placement Ready"
    elif final_score >= 60:
        status = "Moderate"
    else:
        status = "Needs Improvement"

    cur.close()
    conn.close()

    return {
        "attendance": round(attendance, 2),
        "marks": round(marks, 2),
        "skills_count": skill_count,
        "skills_score": skills_score,
        "mock_score": round(mock_score, 2),
        "final_score": round(final_score, 2),
        "status": status,
        "risk_status": risk_status,
    }


def get_top_students(limit=5):
    results = []

    for student in _fetch_students_with_department():
        student_id = student[0]
        student_name = student[1]
        data = calculate_readiness(student_id)

        results.append({
            "student_id": student_id,
            "name": student_name,
            "email": student[2],
            "department": student[3],
            "score": data["final_score"],
            "final_score": data["final_score"],
            "status": data["status"],
        })

    results.sort(key=lambda item: item["score"], reverse=True)

    return results[:limit]


def get_top_students_by_department(limit_per_department=3):
    department_map = {}

    for student_id, name, email, department in _fetch_students_with_department():
        data = calculate_readiness(student_id)
        department_map.setdefault(department, []).append({
            "student_id": student_id,
            "name": name,
            "email": email,
            "department": department,
            "score": data["final_score"],
            "status": data["status"],
        })

    results = []

    for department, students in sorted(department_map.items()):
        students.sort(key=lambda item: item["score"], reverse=True)
        results.append({
            "department": department,
            "students": students[:limit_per_department],
        })

    return results


def get_low_performing_students(threshold=60):
    results = []

    for student_id, name, email, department in _fetch_students_with_department():
        data = calculate_readiness(student_id)

        if data["final_score"] < threshold:
            results.append({
                "student_id": student_id,
                "name": name,
                "email": email,
                "department": department,
                "score": data["final_score"],
                "status": data["status"],
            })

    results.sort(key=lambda item: item["score"])
    return results
