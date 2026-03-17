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