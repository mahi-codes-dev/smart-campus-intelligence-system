from database import get_db_connection
from services.admin_service import get_admin_stats


def get_admin_dashboard():
    stats = get_admin_stats()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM subjects")
    total_subjects = cur.fetchone()[0]
    cur.close()
    conn.close()

    average_score = 0
    if stats["department_average_scores"]:
        total_weighted = sum(
            item["average_score"] * item["student_count"]
            for item in stats["department_average_scores"]
        )
        total_students = sum(item["student_count"] for item in stats["department_average_scores"])
        average_score = round(total_weighted / total_students, 2) if total_students else 0

    top_student = None
    if stats["top_students_by_department"]:
        top_groups = [
            group["students"][0]
            for group in stats["top_students_by_department"]
            if group.get("students")
        ]
        if top_groups:
            top_student = sorted(top_groups, key=lambda item: item["score"], reverse=True)[0]

    return {
        "total_students": stats["total_students"],
        "total_faculty": stats["total_faculty"],
        "total_subjects": total_subjects,
        "top_student": top_student,
        "average_score": average_score,
        "department_average_scores": stats["department_average_scores"],
        "low_performers": stats["low_performers"],
    }
