from database import get_db_connection

def mark_attendance(student_id, subject_id, date, status):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO attendance (student_id, subject_id, date, status)
        VALUES (%s, %s, %s, %s)
    """, (student_id, subject_id, date, status))

    conn.commit()
    cur.close()
    conn.close()


def get_attendance():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT a.id, s.name, sub.name, a.date, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN subjects sub ON a.subject_id = sub.id
    """)

    rows = cur.fetchall()

    attendance_list = []
    for row in rows:
        attendance_list.append({
            "id": row[0],
            "student": row[1],
            "subject": row[2],
            "date": str(row[3]),
            "status": row[4]
        })

    cur.close()
    conn.close()

    return attendance_list