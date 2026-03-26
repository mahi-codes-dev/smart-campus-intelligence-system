print("🔥 THIS FILE IS RUNNING: student_dashboard_service.py")

from database import get_db_connection
from services.mock_service import get_average_mock_score, get_mock_trend
from services.prediction_service import predict_placement_from_score


def get_student_dashboard_data(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Attendance
    cur.execute("""
        SELECT COUNT(*) FILTER (WHERE status = 'Present') * 100.0 / COUNT(*)
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

    # Mock
    mock_score = float(get_average_mock_score(student_id))

    # Final score
    final_score = (attendance * 0.3) + (marks * 0.4) + (mock_score * 0.2) + (skills * 2)

    # Status
    if final_score >= 80:
        status = "Excellent"
        risk_level = "Safe"
    elif final_score >= 60:
        status = "Moderate"
        risk_level = "Warning"
    else:
        status = "At Risk"
        risk_level = "Critical"

    # 🔥 NEW FEATURES
    trend = get_mock_trend(student_id)
    prediction = predict_placement_from_score(student_id, final_score)
    print("DEBUG PREDICTION:", prediction)  # Debug log

    return {
        "attendance": round(attendance, 2),
        "marks": round(marks, 2),
        "mock_score": round(mock_score, 2),
        "skills_score": skills,
        "readiness_score": round(final_score, 2),
        "status": status,
        "risk_level": risk_level,
        "trend": trend,
        "placement_status": prediction["placement_status"]
    }