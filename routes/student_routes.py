from flask import Blueprint, jsonify
from services.student_service import fetch_all_students
from auth.auth_middleware import token_required, role_required
from services.readiness_service import calculate_readiness

student_bp = Blueprint("student_bp", __name__)

# Existing route
@student_bp.route("/students")
@token_required
@role_required("Admin")
def get_students():
    try:
        students = fetch_all_students()
        return jsonify(students), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ NEW DASHBOARD API (CORRECT)
@student_bp.route('/student/dashboard', methods=['GET'])
def student_dashboard_api():
    try:
        student_id = 5  # TEMP

        data = calculate_readiness(student_id)

        return jsonify({
            "readiness_score": data["final_score"],
            "status": data["status"],
            "risk_level": data["risk_status"]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500