from database import get_db_connection
from services.mock_service import get_average_mock_score


def calculate_student_dashboard(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Attendance %
    cur.execute("""
        SELECT 
            COUNT(*) FILTER (WHERE status = 'Present') * 100.0 / COUNT(*) 
        FROM attendance
        WHERE student_id = %s
    """, (student_id,))
    attendance = float(cur.fetchone()[0] or 0)

    # Marks avg
    cur.execute("""
        SELECT AVG(marks)
        FROM marks
        WHERE student_id = %s
    """, (student_id,))
    marks = float(cur.fetchone()[0] or 0)

    # Skills count
    cur.execute("""
        SELECT COUNT(*)
        FROM student_skills
        WHERE student_id = %s
    """, (student_id,))
    skills = cur.fetchone()[0]

    cur.close()
    conn.close()

    # Mock score
    mock_score = float(get_average_mock_score(student_id))

    # Final score
    final_score = (attendance * 0.3) + (marks * 0.4) + (mock_score * 0.2) + (skills * 2)

    if final_score >= 80:
        status = "Excellent"
    elif final_score >= 60:
        status = "Moderate"
    else:
        status = "At Risk"

    return {
        "attendance": round(attendance, 2),
        "marks": round(marks, 2),
        "mock_score": round(mock_score, 2),
        "skills_count": skills,
        "final_score": round(final_score, 2),
        "status": status
    }


def get_all_students_dashboard(filter_status=None,sort_order=None):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM students")
    students = cur.fetchall()

    result = []

    for student in students:
        student_id = student[0]
        name = student[1]

        data = calculate_student_dashboard(student_id)

        # Apply filter
        if filter_status and data["status"].lower() != filter_status.lower():
            continue

        result.append({
            "student_id": student_id,
            "name": name,
            **data
        })

    cur.close()
    conn.close()

    # Apply sorting
    if sort_order == "desc":
        result.sort(key=lambda x: x["final_score"],reverse=True)
    elif sort_order == "asc":
        result.sort(key=lambda x: x["final_score"])

    return result