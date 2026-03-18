from database import get_db_connection

def add_marks(student_id, subject_id, marks, exam_type):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO marks (student_id, subject_id, marks, exam_type)
        VALUES (%s, %s, %s, %s)
    """, (student_id, subject_id, marks, exam_type))

    conn.commit()
    cur.close()
    conn.close()


def get_marks():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT m.id, s.name, sub.name, m.marks, m.exam_type
        FROM marks m
        JOIN students s ON m.student_id = s.id
        JOIN subjects sub ON m.subject_id = sub.id
    """)

    rows = cur.fetchall()

    marks_list = []
    for row in rows:
        marks_list.append({
            "id": row[0],
            "student": row[1],
            "subject": row[2],
            "marks": row[3],
            "exam_type": row[4]
        })

    cur.close()
    conn.close()

    return marks_list