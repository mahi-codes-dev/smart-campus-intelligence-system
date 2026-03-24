from flask import Blueprint, jsonify
from services.student_dashboard_service import get_student_dashboard_data
from auth.auth_middleware import token_required, role_required

student_dashboard_bp = Blueprint("student_dashboard_bp", __name__)


@student_dashboard_bp.route("/student/dashboard/<int:student_id>", methods=["GET"])
@token_required
@role_required("Student")
def student_dashboard(student_id):
    try:
        data = get_student_dashboard_data(student_id)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500