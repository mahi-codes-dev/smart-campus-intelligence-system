from database import get_db_connection


# ✅ ADD ATTENDANCE (DATE AUTO FROM DB)
def mark_attendance(student_id, subject_id, status):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO attendance (student_id, subject_id, status)
        VALUES (%s, %s, %s)
    """, (student_id, subject_id, status))

    conn.commit()
    cur.close()
    conn.close()


# ✅ GET ATTENDANCE FOR SPECIFIC STUDENT
def get_attendance(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT a.id, s.name, sub.name, a.date, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN subjects sub ON a.subject_id = sub.id
        WHERE a.student_id = %s
        ORDER BY a.date DESC
    """, (student_id,))

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