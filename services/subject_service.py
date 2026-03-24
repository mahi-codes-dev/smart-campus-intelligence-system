from database import get_db_connection


def create_subject(name, code, department):
    conn = get_db_connection()
    cur = conn.cursor()

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