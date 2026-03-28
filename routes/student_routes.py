from flask import Blueprint, jsonify, request
from services.student_dashboard_service import get_student_dashboard_data
from services.student_service import fetch_all_students, get_student_record_by_user_id
from auth.auth_middleware import token_required, role_required

student_bp = Blueprint("student_bp", __name__)


@student_bp.route("/students")
@token_required
@role_required("Admin")
def get_students():
    try:
        students = fetch_all_students()
        return jsonify(students), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@student_bp.route("/student/dashboard", methods=["GET"])
@token_required
@role_required("Student")
def student_dashboard_api():
    try:
        student = get_student_record_by_user_id(request.user["user_id"])

        if not student:
            return jsonify({"error": "Student not found"}), 404

        return jsonify(get_student_dashboard_data(student["id"])), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
