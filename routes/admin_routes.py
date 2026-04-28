import logging
logger = logging.getLogger(__name__)
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
from services.institution_service import create_institution, get_institution_context, list_institutions
from services.subject_service import create_subject, delete_subject, get_all_subjects
from services.student_service import create_department, delete_department, get_department_catalog

admin_bp = Blueprint("admin_bp", __name__)


@admin_bp.route("/admin/stats", methods=["GET"])
@token_required
@role_required("Admin")
def fetch_admin_stats(current_user):
    try:
        data = get_admin_stats(institution_id=None if current_user.get("is_super_admin") else current_user.get("institution_id"))
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500


@admin_bp.route("/admin/users", methods=["GET"])
@token_required
@role_required("Admin")
def fetch_admin_users(current_user):
    try:
        users = get_all_users(institution_id=None if current_user.get("is_super_admin") else current_user.get("institution_id"))
        return jsonify(users), 200

    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500


@admin_bp.route("/admin/data-quality", methods=["GET"])
@token_required
@role_required("Admin")
def fetch_admin_data_quality(current_user):
    try:
        return jsonify(
            get_data_quality_snapshot(
                institution_id=None if current_user.get("is_super_admin") else current_user.get("institution_id")
            )
        ), 200

    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500


@admin_bp.route("/admin/operations", methods=["GET"])
@token_required
@role_required("Admin")
def fetch_admin_operations(current_user):
    try:
        return jsonify(
            get_operations_snapshot(
                institution_id=None if current_user.get("is_super_admin") else current_user.get("institution_id")
            )
        ), 200

    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500


@admin_bp.route("/admin/exports/<string:export_name>", methods=["GET"])
@token_required
@role_required("Admin")
def download_admin_export(current_user, export_name):
    try:
        export_payload = build_admin_export(
            export_name,
            institution_id=None if current_user.get("is_super_admin") else current_user.get("institution_id"),
        )
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
        return jsonify({"error": "An internal error occurred"}), 500


@admin_bp.route("/admin/subject", methods=["POST"])
@token_required
@role_required("Admin")
def create_admin_subject(current_user):
    try:
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        code = (data.get("code") or "").strip()
        department = (data.get("department") or "").strip()

        if not name or not code or not department:
            return jsonify({"error": "name, code, and department are required"}), 400

        create_subject(name, code, department, institution_id=current_user.get("institution_id"))
        return jsonify({"message": "Subject added successfully"}), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500


@admin_bp.route("/admin/subjects", methods=["GET"])
@token_required
@role_required("Admin")
def fetch_admin_subjects(current_user):
    try:
        return jsonify(get_all_subjects(institution_id=current_user.get("institution_id"))), 200

    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500


@admin_bp.route("/admin/departments", methods=["GET"])
@token_required
@role_required("Admin")
def fetch_admin_departments(current_user):
    try:
        return jsonify(get_department_catalog(institution_id=current_user.get("institution_id"))), 200

    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500


@admin_bp.route("/admin/department", methods=["POST"])
@token_required
@role_required("Admin")
def create_admin_department(current_user):
    try:
        data = request.get_json() or {}
        department = create_department(data.get("name"), institution_id=current_user.get("institution_id"))
        return jsonify({
            "message": "Department added successfully",
            "department": department,
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500


@admin_bp.route("/admin/department/<int:department_id>", methods=["DELETE"])
@token_required
@role_required("Admin")
def remove_admin_department(current_user, department_id):
    try:
        deleted_department = delete_department(department_id, institution_id=current_user.get("institution_id"))
        return jsonify({
            "message": "Department deleted successfully",
            "department": deleted_department,
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500


@admin_bp.route("/admin/subject/<int:subject_id>", methods=["DELETE"])
@token_required
@role_required("Admin")
def remove_admin_subject(current_user, subject_id):
    try:
        deleted_subject = delete_subject(subject_id, institution_id=current_user.get("institution_id"))
        return jsonify({
            "message": "Subject deleted successfully",
            "subject": deleted_subject,
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500


@admin_bp.route("/admin/user/<int:user_id>", methods=["DELETE"])
@token_required
@role_required("Admin")
def remove_user(current_user, user_id):
    try:
        deleted_user = delete_user(
            user_id,
            current_user_id=request.user["user_id"],
            institution_id=None if current_user.get("is_super_admin") else current_user.get("institution_id"),
        )
        return jsonify({
            "message": "User deleted successfully",
            "user": deleted_user,
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500


@admin_bp.route("/admin/context", methods=["GET"])
@token_required
@role_required("Admin")
def fetch_admin_context(current_user):
    try:
        institution_id = None if current_user.get("is_super_admin") else current_user.get("institution_id")
        context_payload = get_institution_context(institution_id)
        context_payload["viewer"] = {
            "name": current_user.get("name"),
            "is_super_admin": current_user.get("is_super_admin"),
            "institution_code": current_user.get("institution_code"),
        }
        return jsonify(context_payload), 200
    except Exception:
        return jsonify({"error": "An internal error occurred"}), 500


@admin_bp.route("/admin/institutions", methods=["GET"])
@token_required
@role_required("Admin")
def fetch_institutions(current_user):
    if not current_user.get("is_super_admin"):
        return jsonify({"error": "Super admin access required"}), 403

    try:
        return jsonify(list_institutions()), 200
    except Exception:
        return jsonify({"error": "An internal error occurred"}), 500


@admin_bp.route("/admin/institutions", methods=["POST"])
@token_required
@role_required("Admin")
def create_admin_institution(current_user):
    if not current_user.get("is_super_admin"):
        return jsonify({"error": "Super admin access required"}), 403

    try:
        data = request.get_json() or {}
        institution = create_institution(
            data.get("name") or "",
            data.get("code") or "",
            subdomain=data.get("subdomain"),
            plan_name=(data.get("plan_name") or "starter"),
        )
        return jsonify({"message": "Institution created successfully", "institution": institution}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "An internal error occurred"}), 500
