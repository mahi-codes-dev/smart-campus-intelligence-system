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


def save_mock_test(student_id, score, test_name):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id
        FROM mock_tests
        WHERE student_id = %s AND test_name = %s
        ORDER BY created_at DESC NULLS LAST, id DESC
        LIMIT 1
        """,
        (student_id, test_name),
    )
    existing = cur.fetchone()

    if existing:
        cur.execute(
            """
            UPDATE mock_tests
            SET score = %s,
                test_name = %s
            WHERE id = %s
            """,
            (score, test_name, existing[0]),
        )
        action = "updated"
    else:
        cur.execute(
            """
            INSERT INTO mock_tests (student_id, score, test_name)
            VALUES (%s, %s, %s)
            """,
            (student_id, score, test_name),
        )
        action = "created"

    conn.commit()
    cur.close()
    conn.close()

    return action


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


# 🔥 NEW: TREND FUNCTION
def get_mock_trend(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT score
        FROM mock_tests
        WHERE student_id = %s
        ORDER BY created_at DESC
        LIMIT 3
    """, (student_id,))

    scores = [float(row[0]) for row in cur.fetchall()]

    cur.close()
    conn.close()

    if len(scores) < 2:
        return "Not enough data"

    # latest → older
    if len(scores) == 3:
        if scores[0] > scores[1] > scores[2]:
            return "Improving"
        elif scores[0] < scores[1] < scores[2]:
            return "Declining"

    return "Stable"
