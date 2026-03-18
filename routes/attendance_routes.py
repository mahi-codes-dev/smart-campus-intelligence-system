from flask import Blueprint, request, jsonify
from services.attendance_service import mark_attendance, get_attendance
from auth.auth_middleware import token_required, role_required

attendance_bp = Blueprint("attendance_bp", __name__)


@attendance_bp.route("/attendance", methods=["POST"])
@token_required
@role_required("Faculty")
def add_attendance():
    try:
        data = request.get_json()

        student_id = data["student_id"]
        subject_id = data["subject_id"]
        date = data["date"]
        status = data["status"].capitalize()

        mark_attendance(student_id, subject_id, date, status)

        return jsonify({"message": "Attendance marked"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@attendance_bp.route("/attendance", methods=["GET"])
@token_required
def view_attendance():
    try:
        data = get_attendance()
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500