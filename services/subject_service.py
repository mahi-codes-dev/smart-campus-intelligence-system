from database import get_db_connection


def ensure_subject_table_consistency(connection=None):
    conn = connection or get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS subjects (
            id SERIAL PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            code VARCHAR(50) UNIQUE NOT NULL,
            department VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute("ALTER TABLE subjects ADD COLUMN IF NOT EXISTS name VARCHAR(150)")
    cur.execute("ALTER TABLE subjects ADD COLUMN IF NOT EXISTS code VARCHAR(50)")
    cur.execute("ALTER TABLE subjects ADD COLUMN IF NOT EXISTS department VARCHAR(100)")
    cur.execute("ALTER TABLE subjects ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

    if connection is None:
        conn.commit()
        cur.close()
        conn.close()
    else:
        cur.close()


def create_subject(name, code, department):
    conn = get_db_connection()
    cur = conn.cursor()
    ensure_subject_table_consistency(conn)

    # ✅ Check duplicate code
    cur.execute("SELECT id FROM subjects WHERE code = %s", (code,))
    existing = cur.fetchone()

    if existing:
        cur.close()
        conn.close()
        raise Exception("Subject code already exists")

    cur.execute("""
        INSERT INTO subjects (name, code, department)
        VALUES (%s, %s, %s)
    """, (name, code, department))

    conn.commit()
    cur.close()
    conn.close()


def get_all_subjects():
    conn = get_db_connection()
    cur = conn.cursor()
    ensure_subject_table_consistency(conn)

    cur.execute("""
        SELECT id, name, code, department
        FROM subjects
        ORDER BY id ASC
    """)

    rows = cur.fetchall()

    subjects = []
    for row in rows:
        subjects.append({
            "id": row[0],
            "name": row[1],
            "code": row[2],
            "department": row[3]
        })

    cur.close()
    conn.close()

    return subjects


def delete_subject(subject_id):
    conn = get_db_connection()
    cur = conn.cursor()
    ensure_subject_table_consistency(conn)

    cur.execute("SELECT id, name, code FROM subjects WHERE id = %s", (subject_id,))
    subject = cur.fetchone()

    if not subject:
        cur.close()
        conn.close()
        raise ValueError("Subject not found")

    cur.execute("DELETE FROM attendance WHERE subject_id = %s", (subject_id,))
    cur.execute("DELETE FROM marks WHERE subject_id = %s", (subject_id,))
    cur.execute("DELETE FROM subjects WHERE id = %s", (subject_id,))

    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": subject[0],
        "name": subject[1],
        "code": subject[2],
    }
