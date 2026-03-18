from database import get_db_connection

def create_subject(name, code, department):
    conn = get_db_connection()
    cur = conn.cursor()

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

    cur.execute("SELECT * FROM subjects;")
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