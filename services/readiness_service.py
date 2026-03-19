from database import get_db_connection

def calculate_readiness(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Attendance %
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE status = 'Present') * 100.0 / COUNT(*)
        FROM attendance
        WHERE student_id = %s
    """, (student_id,))
    
    attendance_result = float(cur.fetchone()[0] or 0)

    # Marks average
    cur.execute("""
        SELECT AVG(marks)
        FROM marks
        WHERE student_id = %s
    """, (student_id,))
    
    marks_result = float(cur.fetchone()[0] or 0)

    # Final score (Phase 1)
    score = (0.5 * attendance_result) + (0.5 * marks_result)

    # Classification
    if score >= 80:
        status = "Placement Ready"
    elif score >= 60:
        status = "Moderate"
    else:
        status = "Needs Improvement"

    cur.close()
    conn.close()

    return {
        "attendance_percentage": round(attendance_result, 2),
        "marks_average": round(marks_result, 2),
        "final_score": round(score, 2),
        "status": status
    }