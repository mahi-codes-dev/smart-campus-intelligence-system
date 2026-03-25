from flask import Blueprint, jsonify, request
from services.faculty_dashboard_service import get_all_students_dashboard
from auth.auth_middleware import token_required, role_required

faculty_dashboard_bp = Blueprint("faculty_dashboard_bp", __name__)


@faculty_dashboard_bp.route("/faculty/dashboard", methods=["GET"])
@token_required
@role_required("Faculty")
def faculty_dashboard():
    try:
        status_filter = request.args.get("status")
        sort_order = request.args.get("sort")  # Default to descending

        data = get_all_students_dashboard(status_filter, sort_order)

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500