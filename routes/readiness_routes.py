from flask import Blueprint, jsonify
from services.readiness_service import calculate_readiness
from auth.auth_middleware import token_required
from services.readiness_service import get_top_students

readiness_bp = Blueprint("readiness_bp", __name__)


@readiness_bp.route("/readiness/<int:student_id>", methods=["GET"])
@token_required
def get_readiness(student_id):
    try:
        result = calculate_readiness(student_id)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@readiness_bp.route("/top-students", methods=["GET"])
@token_required
def top_students():
    try:
        data = get_top_students()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500