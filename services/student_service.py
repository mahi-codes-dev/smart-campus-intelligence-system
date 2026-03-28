from database import get_db_connection


def ensure_student_table_consistency(connection=None):
    conn = connection or get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            department VARCHAR(100),
            user_id INTEGER
        );
        """
    )

    cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS name VARCHAR(100)")
    cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS email VARCHAR(100)")
    cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS department VARCHAR(100)")
    cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS user_id INTEGER")

    if connection is None:
        conn.commit()
        cur.close()
        conn.close()
    else:
        cur.close()


def sync_student_record(user_id, name, email, department, connection=None):
    conn = connection or get_db_connection()
    cur = conn.cursor()

    ensure_student_table_consistency(conn)

    cur.execute(
        """
        SELECT id
        FROM students
        WHERE user_id = %s OR LOWER(email) = LOWER(%s)
        ORDER BY id ASC
        LIMIT 1
        """,
        (user_id, email),
    )
    existing = cur.fetchone()

    if existing:
        cur.execute(
            """
            UPDATE students
            SET name = %s,
                email = %s,
                department = %s,
                user_id = %s
            WHERE id = %s
            RETURNING id
            """,
            (name, email, department, user_id, existing[0]),
        )
    else:
        cur.execute(
            """
            INSERT INTO students (name, email, department, user_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (name, email, department, user_id),
        )

    student_id = cur.fetchone()[0]

    if connection is None:
        conn.commit()
        cur.close()
        conn.close()
    else:
        cur.close()

    return {
        "id": student_id,
        "user_id": user_id,
        "name": name,
        "email": email,
        "department": department,
    }


def fetch_all_students():
    conn = get_db_connection()
    cur = conn.cursor()

    ensure_student_table_consistency(conn)

    cur.execute(
        """
        SELECT
            s.id,
            COALESCE(NULLIF(s.name, ''), u.name) AS name,
            COALESCE(NULLIF(s.email, ''), u.email) AS email,
            COALESCE(NULLIF(s.department, ''), 'Not Assigned') AS department
        FROM students s
        LEFT JOIN users u ON s.user_id = u.id
        ORDER BY s.id ASC
        """
    )
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
