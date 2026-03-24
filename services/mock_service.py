from database import get_db_connection


def add_mock_test(student_id, score, test_name):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO mock_tests (student_id, score, test_name)
        VALUES (%s, %s, %s)
    """, (student_id, score, test_name))

    conn.commit()
    cur.close()
    conn.close()


def get_mock_scores(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT score, test_name, created_at
        FROM mock_tests
        WHERE student_id = %s
        ORDER BY created_at DESC
    """, (student_id,))

    rows = cur.fetchall()

    results = []
    for row in rows:
        results.append({
            "score": row[0],
            "test_name": row[1],
            "date": str(row[2])
        })

    cur.close()
    conn.close()

    return results


def get_average_mock_score(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT AVG(score)
        FROM mock_tests
        WHERE student_id = %s
    """, (student_id,))

    result = cur.fetchone()[0] or 0

    cur.close()
    conn.close()

    return float(result)