from flask import Blueprint, request, jsonify
from services.attendance_service import mark_attendance, get_attendance
from auth.auth_middleware import token_required, role_required
import jwt

attendance_bp = Blueprint("attendance_bp", __name__)

SECRET_KEY = "smartcampussecret123"


# ✅ ADD ATTENDANCE (FACULTY ONLY)
@attendance_bp.route("/faculty/attendance", methods=["POST"])
@token_required
@role_required("Faculty")
def add_attendance():
    try:
        data = request.get_json()

        # 🔹 Validation
        if not all(k in data for k in ("student_id", "subject_id", "status")):
            return jsonify({"error": "Missing required fields"}), 400

        student_id = data["student_id"]
        subject_id = data["subject_id"]
        status = data["status"].capitalize()

        # 🔹 Insert (date auto handled by DB)
        mark_attendance(student_id, subject_id, status)

        return jsonify({"message": "Attendance marked successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ VIEW ATTENDANCE (STUDENT ONLY)
@attendance_bp.route("/student/attendance", methods=["GET"])
@token_required
@role_required("Student")
def view_attendance():
    try:
        token = request.headers["Authorization"].split(" ")[1]
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        student_id = data["user_id"]  # 🔥 real user mapping

        attendance = get_attendance(student_id)

        return jsonify(attendance), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500