from database import get_db_connection
from services.readiness_service import STUDENT_SCORE_CTE

def get_subject_mentors(subject_id, limit=5):
    """
    Find students who excel in a specific subject.
    Criteria: Marks > 85
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    s.id as student_id,
                    s.name,
                    s.roll_number,
                    s.department,
                    m.marks
                FROM students s
                JOIN marks m ON s.id = m.student_id
                WHERE m.subject_id = %s AND m.marks >= 85
                ORDER BY m.marks DESC, s.name ASC
                LIMIT %s
                """,
                (subject_id, limit)
            )
            rows = cur.fetchall()

    return [
        {
            "student_id": row[0],
            "name": row[1],
            "roll_number": row[2],
            "department": row[3],
            "marks": float(row[4])
        }
        for row in rows
    ]

def get_peer_mentorship_suggestions(student_id):
    """
    Identify subjects where the student is struggling and suggest mentors.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 1. Find subjects where student marks < 60
            cur.execute(
                """
                SELECT
                    m.subject_id,
                    sbj.name as subject_name,
                    m.marks
                FROM marks m
                JOIN subjects sbj ON m.subject_id = sbj.id
                WHERE m.student_id = %s AND m.marks < 60
                ORDER BY m.marks ASC
                """,
                (student_id,)
            )
            struggling_subjects = cur.fetchall()

    suggestions = []
    for sub_id, sub_name, marks in struggling_subjects:
        mentors = get_subject_mentors(sub_id, limit=3)
        if mentors:
            suggestions.append({
                "subject_id": sub_id,
                "subject_name": sub_name,
                "student_marks": float(marks),
                "suggested_mentors": mentors
            })

    return suggestions

def get_mentor_dashboard_stats(student_id):
    """
    Check if the student themselves is a mentor for any subjects.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    sbj.id as subject_id,
                    sbj.name as subject_name,
                    MAX(m.marks) as best_marks
                FROM marks m
                JOIN subjects sbj ON m.subject_id = sbj.id
                WHERE m.student_id = %s
                GROUP BY sbj.id, sbj.name
                HAVING MAX(m.marks) >= 85
                """,
                (student_id,)
            )
            subjects = cur.fetchall()

    return [
        {
            "subject_id": row[0],
            "subject_name": row[1],
            "marks": float(row[2])
        }
        for row in subjects
    ]
