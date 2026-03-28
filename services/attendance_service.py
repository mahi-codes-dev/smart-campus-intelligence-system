from datetime import date, timedelta
from math import gcd

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


def save_attendance_percentage(student_id, subject_id, attendance_percentage):
    percentage = int(round(float(attendance_percentage)))

    if percentage < 0 or percentage > 100:
        raise ValueError("Attendance percentage must be between 0 and 100")

    if percentage == 0:
        present_count = 0
        total_count = 1
    elif percentage == 100:
        present_count = 1
        total_count = 1
    else:
        common_divisor = gcd(percentage, 100)
        present_count = percentage // common_divisor
        total_count = 100 // common_divisor

    absent_count = total_count - present_count
    today = date.today()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM attendance
        WHERE student_id = %s AND subject_id = %s
        """,
        (student_id, subject_id),
    )

    for index in range(present_count):
        cur.execute(
            """
            INSERT INTO attendance (student_id, subject_id, date, status)
            VALUES (%s, %s, %s, %s)
            """,
            (student_id, subject_id, today - timedelta(days=index), "Present"),
        )

    for index in range(absent_count):
        cur.execute(
            """
            INSERT INTO attendance (student_id, subject_id, date, status)
            VALUES (%s, %s, %s, %s)
            """,
            (
                student_id,
                subject_id,
                today - timedelta(days=present_count + index),
                "Absent",
            ),
        )

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
