from flask import Blueprint, Response, jsonify, request

from auth.auth_middleware import token_required, role_required
from services.admin_service import (
    build_admin_export,
    delete_user,
    get_admin_stats,
    get_all_users,
    get_data_quality_snapshot,
    get_operations_snapshot,
)
from services.subject_service import create_subject, delete_subject, get_all_subjects
from services.student_service import create_department, delete_department, get_department_catalog

admin_bp = Blueprint("admin_bp", __name__)


@admin_bp.route("/admin/stats", methods=["GET"])
@token_required
@role_required("Admin")
def fetch_admin_stats():
    try:
        data = get_admin_stats()
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/users", methods=["GET"])
@token_required
@role_required("Admin")
def fetch_admin_users():
    try:
        users = get_all_users()
        return jsonify(users), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/data-quality", methods=["GET"])
@token_required
@role_required("Admin")
def fetch_admin_data_quality():
    try:
        return jsonify(get_data_quality_snapshot()), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/operations", methods=["GET"])
@token_required
@role_required("Admin")
def fetch_admin_operations():
    try:
        return jsonify(get_operations_snapshot()), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/exports/<string:export_name>", methods=["GET"])
@token_required
@role_required("Admin")
def download_admin_export(export_name):
    try:
        export_payload = build_admin_export(export_name)
        return Response(
            export_payload["content"],
            mimetype="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{export_payload["filename"]}"',
                "Cache-Control": "no-store",
            },
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/subject", methods=["POST"])
@token_required
@role_required("Admin")
def create_admin_subject():
    try:
        data = request.get_json() or {}
        print("ADMIN_SUBJECT_CREATE_REQUEST:", data)

        name = (data.get("name") or "").strip()
        code = (data.get("code") or "").strip()
        department = (data.get("department") or "").strip()

        if not name or not code or not department:
            return jsonify({"error": "name, code, and department are required"}), 400

        create_subject(name, code, department)
        return jsonify({"message": "Subject added successfully"}), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/subjects", methods=["GET"])
@token_required
@role_required("Admin")
def fetch_admin_subjects():
    try:
        return jsonify(get_all_subjects()), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/departments", methods=["GET"])
@token_required
@role_required("Admin")
def fetch_admin_departments():
    try:
        return jsonify(get_department_catalog()), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/department", methods=["POST"])
@token_required
@role_required("Admin")
def create_admin_department():
    try:
        data = request.get_json() or {}
        department = create_department(data.get("name"))
        return jsonify({
            "message": "Department added successfully",
            "department": department,
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/department/<int:department_id>", methods=["DELETE"])
@token_required
@role_required("Admin")
def remove_admin_department(department_id):
    try:
        deleted_department = delete_department(department_id)
        return jsonify({
            "message": "Department deleted successfully",
            "department": deleted_department,
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/subject/<int:subject_id>", methods=["DELETE"])
@token_required
@role_required("Admin")
def remove_admin_subject(subject_id):
    try:
        deleted_subject = delete_subject(subject_id)
        return jsonify({
            "message": "Subject deleted successfully",
            "subject": deleted_subject,
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/user/<int:user_id>", methods=["DELETE"])
@token_required
@role_required("Admin")
def remove_user(user_id):
    try:
        print("ADMIN_DELETE_USER_REQUEST:", {"user_id": user_id, "requested_by": request.user["user_id"]})
        deleted_user = delete_user(user_id, current_user_id=request.user["user_id"])
        return jsonify({
            "message": "User deleted successfully",
            "user": deleted_user,
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
