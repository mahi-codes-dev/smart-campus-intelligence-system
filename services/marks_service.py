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


def save_marks(student_id, subject_id, marks, exam_type=None):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id
        FROM marks
        WHERE student_id = %s
          AND subject_id = %s
          AND exam_type IS NOT DISTINCT FROM %s
        ORDER BY created_at DESC NULLS LAST, id DESC
        LIMIT 1
        """,
        (student_id, subject_id, exam_type),
    )
    existing = cur.fetchone()

    if existing:
        cur.execute(
            """
            UPDATE marks
            SET marks = %s,
                exam_type = %s
            WHERE id = %s
            """,
            (marks, exam_type, existing[0]),
        )
        action = "updated"
    else:
        cur.execute(
            """
            INSERT INTO marks (student_id, subject_id, marks, exam_type)
            VALUES (%s, %s, %s, %s)
            """,
            (student_id, subject_id, marks, exam_type),
        )
        action = "created"

    conn.commit()
    cur.close()
    conn.close()

    return action


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
