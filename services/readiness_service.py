from database import get_db_connection


def calculate_readiness(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            COUNT(*) FILTER (WHERE status = 'Present') * 100.0 / COUNT(*)
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
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM students")
    students = cur.fetchall()

    results = []

    for student in students:
        student_id = student[0]
        student_name = student[1]
        data = calculate_readiness(student_id)

        results.append({
            "student_id": student_id,
            "name": student_name,
            "score": data["final_score"],
            "final_score": data["final_score"],
            "status": data["status"],
        })

    results.sort(key=lambda item: item["score"], reverse=True)

    cur.close()
    conn.close()

    return results[:limit]
