from database import get_db_connection
from services.mock_service import get_average_mock_score

def get_student_dashboard_data(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Attendance %
    cur.execute("""
        SELECT 
            COUNT(*) FILTER (WHERE status = 'Present') * 100.0 / COUNT(*) 
        FROM attendance
        WHERE student_id = %s
    """, (student_id,))
    attendance = cur.fetchone()[0] or 0

    # Average Marks
    cur.execute("""
        SELECT AVG(marks)
        FROM marks
        WHERE student_id = %s
    """, (student_id,))
    marks = cur.fetchone()[0] or 0

    # Skills Count
    cur.execute("""
        SELECT COUNT(*)
        FROM student_skills
        WHERE student_id = %s
    """, (student_id,))
    skills = cur.fetchone()[0]

    cur.close()
    conn.close()

    # Mock Score
    mock_score = get_average_mock_score(student_id)

    # Final Score
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