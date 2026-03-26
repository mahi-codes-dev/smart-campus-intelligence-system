from flask import Blueprint, jsonify
from services.admin_dashboard_service import get_admin_dashboard
from auth.auth_middleware import token_required, role_required

admin_dashboard_bp = Blueprint("admin_dashboard_bp", __name__)


@admin_dashboard_bp.route("/admin/dashboard", methods=["GET"])
@token_required
@role_required("Admin")
def admin_dashboard():
    try:
        data = get_admin_dashboard()
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500