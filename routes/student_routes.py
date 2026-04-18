from flask import Blueprint, jsonify, request
import logging

from services.student_dashboard_service import get_student_dashboard_data
from services.student_service import (
    DuplicateStudentError,
    StudentNotFoundError,
    create_student_record,
    delete_student_record,
    ensure_student_table_consistency,
    fetch_all_students,
    get_student_record_by_user_id,
    get_student_profile,
    update_student_record,
)
from services.marks_service import get_subject_wise_marks, get_marks_by_student
from services.attendance_service import get_attendance
from services.skills_service import get_student_skills
from auth.auth_middleware import token_required, role_required
from utils.validators import RequestValidator

logger = logging.getLogger(__name__)
student_bp = Blueprint("student_bp", __name__)


@student_bp.route("/students")
@token_required
@role_required("Admin")
def get_students():
    try:
        students = fetch_all_students()
        return jsonify(students), 200
    except Exception as e:
        logger.exception("get_students failed")
        return jsonify({"error": "An internal error occurred"}), 500


@student_bp.route("/create-table")
@token_required
@role_required("Admin")
def create_table():
    try:
        ensure_student_table_consistency()
        return jsonify({"message": "Students table verified"}), 200
    except Exception as e:
        logger.exception("create_table failed")
        return jsonify({"error": "Failed to verify students table"}), 500


def _validate_student_payload(data):
    validator = RequestValidator(data)
    validator.required("name", "email", "department", "roll_number") \
        .sanitize("name", 100).email("email") \
        .sanitize("department", 100).roll_number("roll_number")
    return validator


@student_bp.route("/add-student", methods=["POST"])
@token_required
@role_required("Admin")
def add_student():
    try:
        validator = _validate_student_payload(request.get_json() or {})
        if validator.has_errors():
            return jsonify({"error": validator.first_error()}), 400

        student = create_student_record(
            validator.validated_data["name"],
            validator.validated_data["email"],
            validator.validated_data["department"],
            validator.validated_data["roll_number"],
        )

        return jsonify({
            "message": "Student added successfully",
            "student": student,
        }), 201

    except DuplicateStudentError as e:
        return jsonify({"error": str(e)}), 409
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("add_student failed")
        return jsonify({"error": "Failed to add student"}), 500


@student_bp.route("/update-student/<int:student_id>", methods=["PUT"])
@token_required
@role_required("Admin")
def update_student(student_id):
    try:
        validator = _validate_student_payload(request.get_json() or {})
        if validator.has_errors():
            return jsonify({"error": validator.first_error()}), 400

        student = update_student_record(
            student_id,
            validator.validated_data["name"],
            validator.validated_data["email"],
            validator.validated_data["department"],
            validator.validated_data["roll_number"],
        )

        return jsonify({
            "message": "Student updated successfully",
            "student": student,
        }), 200

    except StudentNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except DuplicateStudentError as e:
        return jsonify({"error": str(e)}), 409
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("update_student failed")
        return jsonify({"error": "Failed to update student"}), 500


@student_bp.route("/delete-student/<int:student_id>", methods=["DELETE"])
@token_required
@role_required("Admin")
def delete_student(student_id):
    try:
        student = delete_student_record(student_id)
        return jsonify({
            "message": "Student deleted successfully",
            "student": student,
        }), 200

    except StudentNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.exception("delete_student failed")
        return jsonify({"error": "Failed to delete student"}), 500


@student_bp.route("/student/dashboard", methods=["GET"])
@token_required
@role_required("Student")
def student_dashboard_api():
    try:
        student = get_student_record_by_user_id(request.user["user_id"])  # type: ignore

        if not student:
            return jsonify({"error": "Student not found"}), 404

        return jsonify(get_student_dashboard_data(student["id"])), 200

    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500


@student_bp.route("/student/profile", methods=["GET"])
@token_required
@role_required("Student")
def student_profile_api():
    """
    Get comprehensive student profile with all academic and skill data.
    Includes: basic info, performance summary, subject performance, marks history, skills
    """
    try:
        student = get_student_record_by_user_id(request.user["user_id"])  # type: ignore

        if not student:
            return jsonify({"error": "Student not found"}), 404

        student_id = student["id"]
        dashboard = get_student_dashboard_data(student_id)

        return jsonify({
            "profile": get_student_profile(student_id),
            "performance_summary": {
                "readiness_score": dashboard["readiness_score"],
                "status": dashboard["status"],
                "risk_level": dashboard["risk_level"],
                "attendance": dashboard["attendance"],
                "marks": dashboard["marks"],
                "mock_score": dashboard["mock_score"],
                "skills_score": dashboard["skills_score"],
            },
            "subject_performance": get_subject_wise_marks(student_id),
            "marks_history": get_marks_by_student(student_id)[:10],
            "attendance_summary": {
                "attendance_percentage": dashboard["attendance"],
                "recent_records": get_attendance(student_id)[:5],
            },
            "skills": {
                "count": dashboard["skills_count"],
                "score": dashboard["skills_score"],
                "skills_list": get_student_skills(student_id),
            },
            "alerts": dashboard["alerts"],
            "insights": dashboard["insights"],
        }), 200

    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500
