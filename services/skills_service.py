from database import get_db_connection


def add_skill(name):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO skills (name)
        VALUES (%s)
        """,
        (name,),
    )

    conn.commit()
    cur.close()
    conn.close()


def get_or_create_skill(name):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id
        FROM skills
        WHERE LOWER(name) = LOWER(%s)
        """,
        (name,),
    )
    row = cur.fetchone()

    if row:
        skill_id = row[0]
    else:
        cur.execute(
            """
            INSERT INTO skills (name)
            VALUES (%s)
            RETURNING id
            """,
            (name,),
        )
        skill_id = cur.fetchone()[0]
        conn.commit()

    cur.close()
    conn.close()

    return skill_id


def assign_skill(student_id, skill_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 1
        FROM student_skills
        WHERE student_id = %s AND skill_id = %s
        """,
        (student_id, skill_id),
    )

    if cur.fetchone():
        cur.close()
        conn.close()
        return False

    cur.execute(
        """
        INSERT INTO student_skills (student_id, skill_id)
        VALUES (%s, %s)
        """,
        (student_id, skill_id),
    )

    conn.commit()
    cur.close()
    conn.close()

    return True


def get_student_skills(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT DISTINCT sk.name
        FROM student_skills ss
        JOIN skills sk ON ss.skill_id = sk.id
        WHERE ss.student_id = %s
        """,
        (student_id,),
    )

    rows = cur.fetchall()
    skills = [row[0] for row in rows]

    cur.close()
    conn.close()

    return skills
