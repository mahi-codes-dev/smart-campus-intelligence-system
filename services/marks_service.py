from database import get_db_connection
from services.student_service import ensure_student_table_consistency
from services.subject_service import ensure_subject_table_consistency

_MARKS_SCHEMA_READY = False


def ensure_marks_table_consistency(connection=None):
    global _MARKS_SCHEMA_READY

    if _MARKS_SCHEMA_READY:
        return

    conn = connection or get_db_connection()
    cur = conn.cursor()

    ensure_student_table_consistency(conn)
    ensure_subject_table_consistency(conn)

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS marks (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL,
            subject_id INTEGER,
            marks INTEGER,
            exam_type VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute("ALTER TABLE marks ADD COLUMN IF NOT EXISTS student_id INTEGER")
    cur.execute("ALTER TABLE marks ADD COLUMN IF NOT EXISTS subject_id INTEGER")
    cur.execute("ALTER TABLE marks ADD COLUMN IF NOT EXISTS marks INTEGER")
    cur.execute("ALTER TABLE marks ADD COLUMN IF NOT EXISTS exam_type VARCHAR(100)")
    cur.execute("ALTER TABLE marks ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    cur.execute("ALTER TABLE marks DROP CONSTRAINT IF EXISTS marks_student_id_fkey")
    cur.execute("ALTER TABLE marks DROP CONSTRAINT IF EXISTS marks_subject_id_fkey")
    cur.execute(
        """
        ALTER TABLE marks
        ADD CONSTRAINT marks_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id)
        ON DELETE CASCADE
        """
    )
    cur.execute(
        """
        ALTER TABLE marks
        ADD CONSTRAINT marks_subject_id_fkey
        FOREIGN KEY (subject_id) REFERENCES subjects(id)
        ON DELETE CASCADE
        """
    )

    if connection is None:
        conn.commit()
        cur.close()
        conn.close()
    else:
        cur.close()

    _MARKS_SCHEMA_READY = True


def add_marks(student_id, subject_id, marks, exam_type):
    conn = get_db_connection()
    cur = conn.cursor()
    ensure_marks_table_consistency(conn)

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
    ensure_marks_table_consistency(conn)

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
    ensure_marks_table_consistency(conn)

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


def get_subject_wise_marks(student_id):
    conn = get_db_connection()
    cur = conn.cursor()
    ensure_marks_table_consistency(conn)

    cur.execute(
        """
        SELECT
            sub.id,
            sub.name,
            sub.code,
            COALESCE(AVG(m.marks), 0) AS average_marks,
            MAX(m.marks) AS latest_marks
        FROM subjects sub
        LEFT JOIN marks m
            ON m.subject_id = sub.id
           AND m.student_id = %s
        GROUP BY sub.id, sub.name, sub.code
        ORDER BY sub.name ASC
        """,
        (student_id,),
    )
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "subject_id": row[0],
            "subject_name": row[1],
            "subject_code": row[2],
            "average_marks": round(float(row[3] or 0), 2),
            "latest_marks": float(row[4]) if row[4] is not None else None,
        }
        for row in rows
    ]


def get_marks_by_student(student_id):
    conn = get_db_connection()
    cur = conn.cursor()
    ensure_marks_table_consistency(conn)

    cur.execute(
        """
        SELECT
            m.id,
            sub.name,
            sub.code,
            m.marks,
            m.exam_type,
            m.created_at
        FROM marks m
        JOIN subjects sub ON m.subject_id = sub.id
        WHERE m.student_id = %s
        ORDER BY m.created_at DESC NULLS LAST, m.id DESC
        """,
        (student_id,),
    )
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "id": row[0],
            "subject_name": row[1],
            "subject_code": row[2],
            "marks": row[3],
            "exam_type": row[4],
            "date": str(row[5]) if row[5] is not None else None,
        }
        for row in rows
    ]


def get_student_average_marks(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    ensure_marks_table_consistency(conn)

    cur.execute(
        """
        SELECT COALESCE(AVG(marks), 0)
        FROM marks
        WHERE student_id = %s
        """,
        (student_id,),
    )
    average_marks = float(cur.fetchone()[0] or 0)

    cur.close()
    conn.close()

    return round(average_marks, 2)
