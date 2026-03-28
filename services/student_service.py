from database import get_db_connection

_DEPARTMENT_SCHEMA_READY = False
_STUDENT_SCHEMA_READY = False


def ensure_department_table_consistency(connection=None):
    global _DEPARTMENT_SCHEMA_READY

    if _DEPARTMENT_SCHEMA_READY:
        return

    conn = connection or get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS departments (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute("ALTER TABLE departments ADD COLUMN IF NOT EXISTS name VARCHAR(100)")
    cur.execute("ALTER TABLE departments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

    if connection is None:
        conn.commit()
        cur.close()
        conn.close()
    else:
        cur.close()

    _DEPARTMENT_SCHEMA_READY = True


def ensure_department_exists(department, connection=None):
    cleaned_department = (department or "").strip()

    if not cleaned_department:
        return None

    conn = connection or get_db_connection()
    cur = conn.cursor()

    ensure_department_table_consistency(conn)

    cur.execute(
        """
        INSERT INTO departments (name)
        VALUES (%s)
        ON CONFLICT (name) DO NOTHING
        RETURNING id
        """,
        (cleaned_department,),
    )
    inserted = cur.fetchone()

    if inserted is None:
        cur.execute(
            """
            SELECT id
            FROM departments
            WHERE name = %s
            """,
            (cleaned_department,),
        )
        inserted = cur.fetchone()

    if connection is None:
        conn.commit()
        cur.close()
        conn.close()
    else:
        cur.close()

    return {
        "id": inserted[0] if inserted else None,
        "name": cleaned_department,
    }


def ensure_student_table_consistency(connection=None):
    global _STUDENT_SCHEMA_READY

    if _STUDENT_SCHEMA_READY:
        return

    conn = connection or get_db_connection()
    cur = conn.cursor()

    ensure_department_table_consistency(conn)

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

    cur.execute(
        """
        INSERT INTO departments (name)
        SELECT DISTINCT TRIM(department)
        FROM students
        WHERE department IS NOT NULL AND TRIM(department) <> ''
        ON CONFLICT (name) DO NOTHING
        """
    )

    cur.execute("ALTER TABLE students DROP CONSTRAINT IF EXISTS students_user_id_fkey")
    cur.execute("ALTER TABLE students DROP CONSTRAINT IF EXISTS fk_user")
    cur.execute("ALTER TABLE students DROP CONSTRAINT IF EXISTS students_department_fkey")

    cur.execute(
        """
        ALTER TABLE students
        ADD CONSTRAINT students_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
        """
    )

    cur.execute(
        """
        ALTER TABLE students
        ADD CONSTRAINT students_department_fkey
        FOREIGN KEY (department) REFERENCES departments(name)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
        """
    )

    if connection is None:
        conn.commit()
        cur.close()
        conn.close()
    else:
        cur.close()

    _STUDENT_SCHEMA_READY = True


def sync_student_record(user_id, name, email, department, connection=None):
    conn = connection or get_db_connection()
    cur = conn.cursor()

    ensure_student_table_consistency(conn)
    ensure_department_exists(department, conn)

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


def get_all_departments():
    conn = get_db_connection()
    cur = conn.cursor()

    ensure_department_table_consistency(conn)

    cur.execute(
        """
        SELECT name
        FROM departments
        ORDER BY name ASC
        """
    )
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [row[0] for row in rows]


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
