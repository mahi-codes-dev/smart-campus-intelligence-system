from database import get_db_connection
from services.readiness_service import get_top_students


def get_admin_dashboard():
    conn = get_db_connection()
    cur = conn.cursor()

    # Total Students
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]

    # Total Faculty
    cur.execute("""
        SELECT COUNT(*)
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE r.role_name = 'Faculty'
    """)
    total_faculty = cur.fetchone()[0]

    # Total Subjects
    cur.execute("SELECT COUNT(*) FROM subjects")
    total_subjects = cur.fetchone()[0]

    cur.close()
    conn.close()

    # Top Performer
    top_students = get_top_students(1)
    top_student = top_students[0] if top_students else None

    # Average Score (from leaderboard logic)
    all_students = get_top_students(100)
    avg_score = 0

    if all_students:
        total = sum(s["score"] for s in all_students)
        avg_score = total / len(all_students)

    return {
        "total_students": total_students,
        "total_faculty": total_faculty,
        "total_subjects": total_subjects,
        "top_student": top_student,
        "average_score": round(avg_score, 2)
    }