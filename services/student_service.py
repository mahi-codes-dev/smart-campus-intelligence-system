from database import get_db_connection

_DEPARTMENT_SCHEMA_READY = False
_STUDENT_SCHEMA_READY = False


def _table_exists(cur, table_name):
    cur.execute(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
        """,
        (table_name,),
    )
    return cur.fetchone() is not None


def normalize_department_name(department):
    return " ".join((department or "").strip().split())


def normalize_roll_number(roll_number):
    cleaned_roll_number = (roll_number or "").strip().upper()
    return cleaned_roll_number


def ensure_roll_number_available(roll_number, connection=None, exclude_student_id=None):
    normalized_roll_number = normalize_roll_number(roll_number)

    if not normalized_roll_number:
        return None

    conn = connection or get_db_connection()
    cur = conn.cursor()

    ensure_student_table_consistency(conn)

    query = """
        SELECT id
        FROM students
        WHERE LOWER(COALESCE(roll_number, '')) = LOWER(%s)
    """
    params = [normalized_roll_number]

    if exclude_student_id is not None:
        query += " AND id <> %s"
        params.append(exclude_student_id)

    cur.execute(query, tuple(params))
    existing = cur.fetchone()

    if connection is None:
        cur.close()
        conn.close()
    else:
        cur.close()

    if existing:
        raise ValueError(f"Roll number {normalized_roll_number} is already assigned to another student")

    return normalized_roll_number


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
    cleaned_department = normalize_department_name(department)

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


def require_department_exists(department, connection=None):
    cleaned_department = normalize_department_name(department)

    if not cleaned_department:
        raise ValueError("Department is required")

    conn = connection or get_db_connection()
    cur = conn.cursor()

    ensure_department_table_consistency(conn)
    cur.execute(
        """
        SELECT id, name
        FROM departments
        WHERE LOWER(name) = LOWER(%s)
        """,
        (cleaned_department,),
    )
    existing = cur.fetchone()

    if connection is None:
        cur.close()
        conn.close()
    else:
        cur.close()

    if not existing:
        raise ValueError("Select a valid department from the department list")

    return {
        "id": existing[0],
        "name": existing[1],
    }


def create_department(department, connection=None):
    cleaned_department = normalize_department_name(department)

    if not cleaned_department:
        raise ValueError("Department name is required")

    conn = connection or get_db_connection()
    cur = conn.cursor()

    ensure_department_table_consistency(conn)
    cur.execute(
        """
        SELECT id, name
        FROM departments
        WHERE LOWER(name) = LOWER(%s)
        """,
        (cleaned_department,),
    )
    existing = cur.fetchone()

    if existing:
        if connection is None:
            cur.close()
            conn.close()
        else:
            cur.close()
        raise ValueError(f"Department {existing[1]} already exists")

    cur.execute(
        """
        INSERT INTO departments (name)
        VALUES (%s)
        RETURNING id, name
        """,
        (cleaned_department,),
    )
    created = cur.fetchone()

    if connection is None:
        conn.commit()
        cur.close()
        conn.close()
    else:
        cur.close()

    return {
        "id": created[0],
        "name": created[1],
    }


def get_department_catalog():
    conn = get_db_connection()
    cur = conn.cursor()

    ensure_department_table_consistency(conn)
    subjects_table_exists = _table_exists(cur, "subjects")

    subject_join = "LEFT JOIN subjects sub ON sub.department = d.name" if subjects_table_exists else ""
    subject_count = "COUNT(DISTINCT sub.id) AS subject_count" if subjects_table_exists else "0 AS subject_count"
    cur.execute(
        f"""
        SELECT
            d.id,
            d.name,
            COUNT(DISTINCT s.id) AS student_count,
            {subject_count}
        FROM departments d
        LEFT JOIN students s ON s.department = d.name
        {subject_join}
        GROUP BY d.id, d.name
        ORDER BY d.name ASC
        """
    )
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "student_count": row[2],
            "subject_count": row[3],
        }
        for row in rows
    ]


def delete_department(department_id):
    conn = get_db_connection()
    cur = conn.cursor()

    ensure_department_table_consistency(conn)
    cur.execute(
        """
        SELECT id, name
        FROM departments
        WHERE id = %s
        """,
        (department_id,),
    )
    department = cur.fetchone()

    if not department:
        cur.close()
        conn.close()
        raise ValueError("Department not found")

    cur.execute("SELECT COUNT(*) FROM students WHERE department = %s", (department[1],))
    student_count = cur.fetchone()[0]
    if _table_exists(cur, "subjects"):
        cur.execute("SELECT COUNT(*) FROM subjects WHERE department = %s", (department[1],))
        subject_count = cur.fetchone()[0]
    else:
        subject_count = 0

    if student_count or subject_count:
        cur.close()
        conn.close()
        raise ValueError(
            f"Cannot delete department {department[1]} because it is linked to "
            f"{student_count} students and {subject_count} subjects"
        )

    cur.execute("DELETE FROM departments WHERE id = %s", (department_id,))
    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": department[0],
        "name": department[1],
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
            roll_number VARCHAR(50),
            department VARCHAR(100),
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS name VARCHAR(100)")
    cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS email VARCHAR(100)")
    cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS roll_number VARCHAR(50)")
    cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS department VARCHAR(100)")
    cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS user_id INTEGER")
    cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

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

    if _table_exists(cur, "users"):
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


def sync_student_record(user_id, name, email, department, roll_number=None, connection=None):
    conn = connection or get_db_connection()
    cur = conn.cursor()
    normalized_roll_number = normalize_roll_number(roll_number)
    department_record = require_department_exists(department, connection=conn)

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

    if normalized_roll_number:
        ensure_roll_number_available(
            normalized_roll_number,
            connection=conn,
            exclude_student_id=existing[0] if existing else None,
        )

    if existing:
        cur.execute(
            """
            UPDATE students
            SET name = %s,
                email = %s,
                roll_number = COALESCE(NULLIF(%s, ''), roll_number),
                department = %s,
                user_id = %s
            WHERE id = %s
            RETURNING id, roll_number
            """,
            (name, email, normalized_roll_number, department_record["name"], user_id, existing[0]),
        )
    else:
        cur.execute(
            """
            INSERT INTO students (name, email, roll_number, department, user_id)
            VALUES (%s, %s, NULLIF(%s, ''), %s, %s)
            RETURNING id, roll_number
            """,
            (name, email, normalized_roll_number, department_record["name"], user_id),
        )

    result = cur.fetchone()
    student_id = result[0] if result else None
    saved_roll_number = result[1] if result else normalized_roll_number

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
        "roll_number": saved_roll_number,
        "department": department_record["name"],
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
            COALESCE(NULLIF(s.roll_number, ''), 'Not Assigned') AS roll_number,
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
            "roll_number": row[3],
            "department": row[4]
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
            s.user_id,
            COALESCE(NULLIF(s.name, ''), u.name) AS name,
            COALESCE(NULLIF(s.email, ''), u.email) AS email,
            COALESCE(NULLIF(s.roll_number, ''), 'Not Assigned') AS roll_number,
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
        "user_id": row[1],
        "name": row[2],
        "email": row[3],
        "roll_number": row[4],
        "department": row[5],
    }


def get_student_profile(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            s.id,
            s.user_id,
            COALESCE(NULLIF(s.name, ''), u.name) AS name,
            COALESCE(NULLIF(s.email, ''), u.email) AS email,
            COALESCE(NULLIF(s.roll_number, ''), 'Not Assigned') AS roll_number,
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
        "user_id": row[1],
        "name": row[2],
        "email": row[3],
        "roll_number": row[4],
        "department": row[5],
    }
