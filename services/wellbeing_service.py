from database import get_db_connection
from datetime import datetime, timedelta

def ensure_wellbeing_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS student_wellbeing (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            stress_level INTEGER NOT NULL CHECK (stress_level >= 1 AND stress_level <= 5),
            mood VARCHAR(50),
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    cur.close()
    conn.close()

def save_wellbeing_entry(student_id, stress_level, mood=None, note=None):
    ensure_wellbeing_table()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO student_wellbeing (student_id, stress_level, mood, note)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (student_id, stress_level, mood, note)
    )
    entry_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return entry_id

def get_student_wellbeing_history(student_id, limit=30):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT stress_level, mood, note, created_at
        FROM student_wellbeing
        WHERE student_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (student_id, limit)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "stress_level": row[0],
            "mood": row[1],
            "note": row[2],
            "created_at": row[3].isoformat()
        }
        for row in rows
    ]

def get_class_wellbeing_summary(department=None):
    """
    Get average stress levels for a department or campus-wide.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
        SELECT AVG(w.stress_level) as avg_stress, COUNT(*) as entry_count
        FROM student_wellbeing w
        JOIN students s ON w.student_id = s.id
        WHERE w.created_at >= %s
    """
    # Last 7 days
    params = [datetime.now() - timedelta(days=7)]
    
    if department:
        query += " AND s.department = %s"
        params.append(department)
        
    cur.execute(query, tuple(params))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    return {
        "average_stress_7d": float(row[0]) if row[0] else 0,
        "entry_count_7d": row[1]
    }
