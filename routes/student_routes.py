from flask import Blueprint, jsonify, request
from services.student_service import fetch_all_students
from auth.auth_middleware import token_required, role_required
from services.readiness_service import calculate_readiness
from database import get_db_connection

student_bp = Blueprint("student_bp", __name__)


# ✅ EXISTING ADMIN ROUTE (NO CHANGE)
@student_bp.route("/students")
@token_required
@role_required("Admin")
@role_required("Student")  # 🔥 ALLOW STUDENTS TO ACCESS THIS TOO
def get_students():
    try:
        students = fetch_all_students()
        return jsonify(students), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ UPDATED DASHBOARD ROUTE (REAL IMPLEMENTATION)
@student_bp.route('/student/dashboard', methods=['GET'])
@token_required
def student_dashboard_api():
    try:
        # 🔥 Get user from JWT
        user = request.user
        user_id = user["user_id"]

        conn = get_db_connection()
        cur = conn.cursor()

        # 🔥 Find student_id using user_id
        cur.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
        student = cur.fetchone()

        if not student:
            return jsonify({"error": "Student not found"}), 404

        student_id = student[0]

        # 🔥 Calculate readiness
        data = calculate_readiness(student_id)

        cur.close()
        conn.close()

        return jsonify({
            "readiness_score": data["final_score"],
            "status": data["status"],
            "risk_level": data["risk_status"],
            "attendance": data["attendance"],
            "marks": data["marks"],
            "skills_score": data["skills_score"],
            "mock_score": data["mock_score"]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500