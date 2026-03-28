from flask import Blueprint, request, jsonify
from services.attendance_service import (
    mark_attendance,
    get_attendance,
    save_attendance_percentage,
)
from auth.auth_middleware import token_required, role_required
from services.student_service import get_student_record_by_user_id

attendance_bp = Blueprint("attendance_bp", __name__)


# ✅ ADD ATTENDANCE (FACULTY ONLY)
@attendance_bp.route("/faculty/attendance", methods=["POST"])
@token_required
@role_required("Faculty")
def add_attendance():
    try:
        data = request.get_json() or {}
        print("FACULTY_ATTENDANCE_REQUEST:", data)

        if not all(k in data for k in ("student_id", "subject_id")):
            return jsonify({"error": "Missing required fields"}), 400

        student_id = data["student_id"]
        subject_id = data["subject_id"]

        if "attendance_percentage" in data:
            save_attendance_percentage(
                student_id,
                subject_id,
                data["attendance_percentage"],
            )

            return jsonify({
                "message": "Attendance percentage saved successfully",
                "student_id": student_id,
                "subject_id": subject_id,
                "attendance_percentage": int(round(float(data["attendance_percentage"]))),
            }), 200

        if "status" not in data:
            return jsonify({"error": "status or attendance_percentage is required"}), 400

        status = str(data["status"]).capitalize()

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
        student = get_student_record_by_user_id(request.user["user_id"])
        if not student:
            return jsonify({"error": "Student not found"}), 404

        attendance = get_attendance(student["id"])

        return jsonify(attendance), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

