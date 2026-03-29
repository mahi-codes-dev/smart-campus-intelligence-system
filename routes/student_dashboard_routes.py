from flask import Blueprint, jsonify, request, g
from services.student_dashboard_service import get_student_dashboard_data
from services.student_service import get_student_record_by_user_id
from auth.auth_middleware import token_required, role_required

student_dashboard_bp = Blueprint("student_dashboard_bp", __name__)


@student_dashboard_bp.route("/student/dashboard", methods=["GET"])
@token_required
@role_required("Student")
def student_dashboard():
    try:
        student = get_student_record_by_user_id(g.user["user_id"])

        if not student:
            return jsonify({"error": "Student not found"}), 404

        return jsonify(get_student_dashboard_data(student["id"])), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
