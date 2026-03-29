from flask import Blueprint, jsonify, request
from services.student_dashboard_service import get_student_dashboard_data
from services.student_service import fetch_all_students, get_student_record_by_user_id, get_student_profile
from services.marks_service import get_subject_wise_marks, get_marks_by_student
from services.attendance_service import get_attendance
from services.skills_service import get_student_skills
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
        student = get_student_record_by_user_id(request.user["user_id"])  # type: ignore

        if not student:
            return jsonify({"error": "Student not found"}), 404

        return jsonify(get_student_dashboard_data(student["id"])), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        return jsonify({"error": str(e)}), 500
