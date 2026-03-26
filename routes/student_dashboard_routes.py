from flask import Blueprint, jsonify, request
from services.student_dashboard_service import get_student_dashboard_data
from auth.auth_middleware import token_required, role_required
from database import get_db_connection

student_dashboard_bp = Blueprint("student_dashboard_bp", __name__)

@student_dashboard_bp.route("/student/dashboard", methods=["GET"])
@token_required
@role_required("Student")
def student_dashboard():
    try:
        user_id = request.user["user_id"]

        # Map user → student
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
        student = cur.fetchone()

        if not student:
            return jsonify({"error": "Student not found"}), 404

        student_id = student[0]

        data = get_student_dashboard_data(student_id)

        cur.close()
        conn.close()

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500