from flask import Blueprint, jsonify, request
from services.faculty_dashboard_service import (
    get_all_students_dashboard,
    get_classroom_roster,
    get_faculty_dashboard_summary,
    save_classroom_attendance,
    save_classroom_marks,
    get_student_detail,
)
from auth.auth_middleware import token_required, role_required

faculty_dashboard_bp = Blueprint("faculty_dashboard_bp", __name__)


@faculty_dashboard_bp.route("/faculty/dashboard", methods=["GET"])
@token_required
@role_required("Faculty")
def faculty_dashboard():
    try:
        status_filter = request.args.get("status")
        sort_order = request.args.get("sort")
        search = request.args.get("search")
        department = request.args.get("department")

        data = get_all_students_dashboard(
            filter_status=status_filter,
            sort_order=sort_order,
            search=search,
            department=department,
        )

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@faculty_dashboard_bp.route("/faculty/summary", methods=["GET"])
@token_required
@role_required("Faculty")
def faculty_summary():
    try:
        status_filter = request.args.get("status")
        sort_order = request.args.get("sort")
        search = request.args.get("search")
        department = request.args.get("department")

        return jsonify(
            get_faculty_dashboard_summary(
                search=search,
                department=department,
                filter_status=status_filter,
                sort_order=sort_order,
            )
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@faculty_dashboard_bp.route("/faculty/student/<int:student_id>", methods=["GET"])
@token_required
@role_required("Faculty")
def faculty_student_detail(student_id):
    try:
        return jsonify(get_student_detail(student_id)), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@faculty_dashboard_bp.route("/faculty/classroom", methods=["GET"])
@token_required
@role_required("Faculty")
def faculty_classroom():
    try:
        subject_id = request.args.get("subject_id", type=int)
        if not subject_id:
            return jsonify({"error": "subject_id is required"}), 400

        return jsonify(
            get_classroom_roster(
                subject_id=subject_id,
                department=request.args.get("department"),
                search=request.args.get("search"),
            )
        ), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@faculty_dashboard_bp.route("/faculty/classroom/attendance", methods=["POST"])
@token_required
@role_required("Faculty")
def faculty_classroom_attendance():
    try:
        data = request.get_json() or {}

        if "subject_id" not in data:
            return jsonify({"error": "subject_id is required"}), 400

        result = save_classroom_attendance(data["subject_id"], data.get("entries") or [])
        return jsonify({
            "message": "Class attendance saved successfully",
            **result,
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@faculty_dashboard_bp.route("/faculty/classroom/marks", methods=["POST"])
@token_required
@role_required("Faculty")
def faculty_classroom_marks():
    try:
        data = request.get_json() or {}

        if "subject_id" not in data:
            return jsonify({"error": "subject_id is required"}), 400

        result = save_classroom_marks(
            data["subject_id"],
            data.get("exam_type"),
            data.get("entries") or [],
        )
        return jsonify({
            "message": "Class marks saved successfully",
            **result,
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
