from database import get_db_connection


def add_skill(name):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO skills (name)
        VALUES (%s)
    """, (name,))

    conn.commit()
    cur.close()
    conn.close()


def assign_skill(student_id, skill_id):
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
        SELECT DISTINCT sk.name
        FROM student_skills ss
        JOIN skills sk ON ss.skill_id = sk.id
        WHERE ss.student_id = %s
    """, (student_id,))

    rows = cur.fetchall()

    skills = [row[0] for row in rows]

    cur.close()
    conn.close()

    return skills