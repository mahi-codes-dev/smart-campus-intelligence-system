from database import get_db_connection
from services.readiness_service import (
    get_department_average_scores,
    get_low_performing_students,
    get_top_students_by_department,
)
from services.student_service import get_all_departments, get_department_catalog


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
    conn.close()

    department_average_scores = get_department_average_scores()

    return {
        "total_students": total_students,
        "total_faculty": total_faculty,
        "total_users": total_users,
        "total_departments": len(get_department_catalog()),
        "top_students_by_department": get_top_students_by_department(),
        "low_performers": get_low_performing_students(),
        "department_average_scores": department_average_scores,
        "departments": [item["department"] for item in department_average_scores] or get_all_departments(),
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


def get_data_quality_snapshot():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*)
        FROM students
        WHERE roll_number IS NULL OR TRIM(roll_number) = ''
        """
    )
    missing_roll_numbers = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*)
        FROM students
        WHERE department IS NULL OR TRIM(department) = ''
        """
    )
    missing_departments = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT UPPER(TRIM(roll_number))
            FROM students
            WHERE roll_number IS NOT NULL AND TRIM(roll_number) <> ''
            GROUP BY UPPER(TRIM(roll_number))
            HAVING COUNT(*) > 1
        ) duplicate_roll_numbers
        """
    )
    duplicate_roll_number_groups = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT LOWER(email)
            FROM users
            WHERE email IS NOT NULL AND TRIM(email) <> ''
            GROUP BY LOWER(email)
            HAVING COUNT(*) > 1
        ) duplicate_user_emails
        """
    )
    duplicate_user_email_groups = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*)
        FROM students s
        LEFT JOIN users u ON s.user_id = u.id
        WHERE s.user_id IS NOT NULL AND u.id IS NULL
        """
    )
    orphan_student_links = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*)
        FROM students s
        WHERE NOT EXISTS (SELECT 1 FROM attendance a WHERE a.student_id = s.id)
          AND NOT EXISTS (SELECT 1 FROM marks m WHERE m.student_id = s.id)
          AND NOT EXISTS (SELECT 1 FROM mock_tests mt WHERE mt.student_id = s.id)
          AND NOT EXISTS (SELECT 1 FROM student_skills sk WHERE sk.student_id = s.id)
        """
    )
    students_without_activity = cur.fetchone()[0]

    cur.close()
    conn.close()

    issue_total = (
        missing_roll_numbers
        + missing_departments
        + duplicate_roll_number_groups
        + duplicate_user_email_groups
        + orphan_student_links
        + students_without_activity
    )

    if issue_total == 0:
        status = "Healthy"
    elif issue_total <= max(3, total_students // 10):
        status = "Needs Review"
    else:
        status = "Attention Needed"

    return {
        "status": status,
        "total_students": total_students,
        "missing_roll_numbers": missing_roll_numbers,
        "missing_departments": missing_departments,
        "duplicate_roll_number_groups": duplicate_roll_number_groups,
        "duplicate_user_email_groups": duplicate_user_email_groups,
        "orphan_student_links": orphan_student_links,
        "students_without_activity": students_without_activity,
        "issue_total": issue_total,
    }


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
