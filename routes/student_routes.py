from flask import Blueprint, jsonify, request
from database import get_db_connection
import psycopg2

student_bp = Blueprint("student_bp", __name__)

@student_bp.route("/students")
def get_students():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM students;")
        rows = cur.fetchall()

        students = []
        for row in rows:
            students.append({
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "department": row[3]
            })

        cur.close()
        conn.close()

        return jsonify(students)

    except Exception as e:
        return jsonify({"error": str(e)}), 500