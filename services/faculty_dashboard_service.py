from database import get_db_connection
from services.mock_service import get_average_mock_score, get_mock_trend


def calculate_student_dashboard(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Attendance
    cur.execute("""
        SELECT COUNT(*) FILTER (WHERE status = 'Present') * 100.0 / NULLIF(COUNT(*), 0)
        FROM attendance
        WHERE student_id = %s
    """, (student_id,))
    attendance = float(cur.fetchone()[0] or 0)

    # Marks
    cur.execute("""
        SELECT AVG(marks)
        FROM marks
        WHERE student_id = %s
    """, (student_id,))
    marks = float(cur.fetchone()[0] or 0)

    # Skills
    cur.execute("""
        SELECT COUNT(*)
        FROM student_skills
        WHERE student_id = %s
    """, (student_id,))
    skills = cur.fetchone()[0]

    cur.close()
    conn.close()

    mock_score = float(get_average_mock_score(student_id))

    final_score = (attendance * 0.3) + (marks * 0.4) + (mock_score * 0.2) + (skills * 2)

    if final_score >= 80:
        status = "Excellent"
    elif final_score >= 60:
        status = "Moderate"
    else:
        status = "At Risk"

    # 🔥 TREND
    trend = get_mock_trend(student_id)

    return {
        "attendance": round(attendance, 2),
        "marks": round(marks, 2),
        "mock_score": round(mock_score, 2),
        "skills_count": skills,
        "final_score": round(final_score, 2),
        "status": status,
        "trend": trend
    }


def get_all_students_dashboard(filter_status=None, sort_order=None):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            s.id,
            COALESCE(NULLIF(s.name, ''), u.name) AS name,
            COALESCE(NULLIF(s.email, ''), u.email) AS email,
            COALESCE(s.department, 'Not Assigned') AS department
        FROM students s
        LEFT JOIN users u ON s.user_id = u.id
        ORDER BY s.id ASC
        """
    )
    students = cur.fetchall()

    result = []

    for student in students:
        student_id, name, email, department = student

        data = calculate_student_dashboard(student_id)

        if filter_status and data["status"].lower() != filter_status.lower():
            continue

        result.append({
            "id": student_id,
            "student_id": student_id,
            "name": name,
            "email": email,
            "department": department,
            **data
        })

    cur.close()
    conn.close()

    # Sorting
    if sort_order == "desc":
        result.sort(key=lambda x: x["final_score"], reverse=True)
    elif sort_order == "asc":
        result.sort(key=lambda x: x["final_score"])

    return result
