from database import get_db_connection


def fetch_all_students():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM students;")
    rows = cur.fetchall()

    students = []
    for row in rows:
        students.append({
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "department": row[3]
        })

    cur.close()
    conn.close()

    return students


def get_student_record_by_user_id(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            s.id,
            COALESCE(NULLIF(s.name, ''), u.name) AS name,
            COALESCE(NULLIF(s.email, ''), u.email) AS email,
            COALESCE(s.department, 'Not Assigned') AS department
        FROM students s
        LEFT JOIN users u ON s.user_id = u.id
        WHERE s.user_id = %s
        """,
        (user_id,),
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "department": row[3],
    }


def get_student_profile(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            s.id,
            COALESCE(NULLIF(s.name, ''), u.name) AS name,
            COALESCE(NULLIF(s.email, ''), u.email) AS email,
            COALESCE(s.department, 'Not Assigned') AS department
        FROM students s
        LEFT JOIN users u ON s.user_id = u.id
        WHERE s.id = %s
        """,
        (student_id,),
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "department": row[3],
    }
