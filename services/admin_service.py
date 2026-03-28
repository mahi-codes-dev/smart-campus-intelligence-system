from database import get_db_connection


STUDENT_SCORE_CTE = """
WITH attendance_stats AS (
    SELECT
        student_id,
        COUNT(*) FILTER (WHERE status = 'Present') * 100.0 / NULLIF(COUNT(*), 0) AS attendance_score
    FROM attendance
    GROUP BY student_id
),
marks_stats AS (
    SELECT
        student_id,
        AVG(marks) AS marks_score
    FROM marks
    GROUP BY student_id
),
skills_stats AS (
    SELECT
        student_id,
        LEAST(COUNT(*) * 10, 100) AS skills_score
    FROM student_skills
    GROUP BY student_id
),
mock_stats AS (
    SELECT
        student_id,
        AVG(score) AS mock_score
    FROM mock_tests
    GROUP BY student_id
),
student_scores AS (
    SELECT
        s.id AS student_id,
        COALESCE(NULLIF(s.name, ''), u.name) AS name,
        COALESCE(NULLIF(s.email, ''), u.email) AS email,
        COALESCE(NULLIF(s.department, ''), 'Not Assigned') AS department,
        COALESCE(a.attendance_score, 0) AS attendance,
        COALESCE(m.marks_score, 0) AS marks,
        COALESCE(sk.skills_score, 0) AS skills_score,
        COALESCE(mt.mock_score, 0) AS mock_score,
        ROUND(
            (COALESCE(a.attendance_score, 0) * 0.3) +
            (COALESCE(m.marks_score, 0) * 0.4) +
            (COALESCE(sk.skills_score, 0) * 0.2) +
            (COALESCE(mt.mock_score, 0) * 0.1),
            2
        ) AS final_score
    FROM students s
    LEFT JOIN users u ON s.user_id = u.id
    LEFT JOIN attendance_stats a ON a.student_id = s.id
    LEFT JOIN marks_stats m ON m.student_id = s.id
    LEFT JOIN skills_stats sk ON sk.student_id = s.id
    LEFT JOIN mock_stats mt ON mt.student_id = s.id
)
"""


def _format_status(score):
    if score >= 80:
        return "Placement Ready"
    if score >= 60:
        return "Moderate"
    return "Needs Improvement"


def _fetch_top_students_by_department(limit_per_department=3, connection=None):
    conn = connection or get_db_connection()
    cur = conn.cursor()

    cur.execute(
        STUDENT_SCORE_CTE
        + """
        SELECT
            department,
            student_id,
            name,
            email,
            final_score
        FROM (
            SELECT
                student_scores.*,
                ROW_NUMBER() OVER (
                    PARTITION BY department
                    ORDER BY final_score DESC, name ASC, student_id ASC
                ) AS department_rank
            FROM student_scores
        ) ranked_scores
        WHERE department_rank <= %s
        ORDER BY department ASC, final_score DESC, name ASC, student_id ASC
        """,
        (limit_per_department,),
    )
    rows = cur.fetchall()
    cur.close()

    if connection is None:
        conn.close()

    grouped = []
    current_department = None

    for row in rows:
        department = row[0]
        score = float(row[4] or 0)

        if department != current_department:
            grouped.append({
                "department": department,
                "students": [],
            })
            current_department = department

        grouped[-1]["students"].append({
            "student_id": row[1],
            "name": row[2],
            "email": row[3],
            "department": department,
            "score": score,
            "status": _format_status(score),
        })

    return grouped


def _fetch_low_performers(threshold=60, connection=None):
    conn = connection or get_db_connection()
    cur = conn.cursor()

    cur.execute(
        STUDENT_SCORE_CTE
        + """
        SELECT
            student_id,
            name,
            email,
            department,
            final_score
        FROM student_scores
        WHERE final_score < %s
        ORDER BY final_score ASC, name ASC, student_id ASC
        """,
        (threshold,),
    )
    rows = cur.fetchall()
    cur.close()

    if connection is None:
        conn.close()

    return [
        {
            "student_id": row[0],
            "name": row[1],
            "email": row[2],
            "department": row[3],
            "score": float(row[4] or 0),
            "status": _format_status(float(row[4] or 0)),
        }
        for row in rows
    ]


def get_admin_stats():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*)
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE LOWER(r.role_name) = 'faculty'
        """
    )
    total_faculty = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.close()
    top_students_by_department = _fetch_top_students_by_department(connection=conn)
    low_performers = _fetch_low_performers(connection=conn)
    conn.close()

    return {
        "total_students": total_students,
        "total_faculty": total_faculty,
        "total_users": total_users,
        "top_students_by_department": top_students_by_department,
        "low_performers": low_performers,
    }


def get_all_users():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            u.id,
            u.name,
            u.email,
            r.role_name
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        ORDER BY u.id ASC
        """
    )
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "role": row[3] or "Unknown",
        }
        for row in rows
    ]


def delete_user(user_id, current_user_id=None):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT u.id, u.email, COALESCE(r.role_name, '')
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        WHERE u.id = %s
        """,
        (user_id,),
    )
    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()
        raise ValueError("User not found")

    if current_user_id is not None and int(user_id) == int(current_user_id):
        cur.close()
        conn.close()
        raise ValueError("You cannot delete your own account")

    role_name = (user[2] or "").strip().lower()

    if role_name == "admin":
        cur.execute(
            """
            SELECT COUNT(*)
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE LOWER(r.role_name) = 'admin'
            """
        )
        admin_count = cur.fetchone()[0]

        if admin_count <= 1:
            cur.close()
            conn.close()
            raise ValueError("At least one admin account must remain in the system")

    cur.execute(
        """
        SELECT id
        FROM students
        WHERE user_id = %s OR LOWER(email) = LOWER(%s)
        ORDER BY id ASC
        """,
        (user_id, user[1]),
    )
    student_ids = [row[0] for row in cur.fetchall()]

    for student_id in student_ids:
        cur.execute("DELETE FROM attendance WHERE student_id = %s", (student_id,))
        cur.execute("DELETE FROM marks WHERE student_id = %s", (student_id,))
        cur.execute("DELETE FROM mock_tests WHERE student_id = %s", (student_id,))
        cur.execute("DELETE FROM student_skills WHERE student_id = %s", (student_id,))

    if student_ids:
        cur.execute(
            """
            DELETE FROM students
            WHERE user_id = %s OR LOWER(email) = LOWER(%s)
            """,
            (user_id, user[1]),
        )

    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    deleted = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    if not deleted:
        raise ValueError("User could not be deleted")

    return {
        "id": user[0],
        "email": user[1],
        "role": user[2] or "Unknown",
    }
