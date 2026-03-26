from database import get_db_connection


def add_student_skill(student_id, skill_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO student_skills (student_id, skill_id)
        VALUES (%s, %s)
    """, (student_id, skill_id))

    conn.commit()
    cur.close()
    conn.close()


def get_student_skills(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.id, s.name
        FROM student_skills ss
        JOIN skills s ON ss.skill_id = s.id
        WHERE ss.student_id = %s
    """, (student_id,))

    rows = cur.fetchall()

    skills = []
    for row in rows:
        skills.append({
            "skill_id": row[0],
            "skill_name": row[1]
        })

    cur.close()
    conn.close()

    return skills