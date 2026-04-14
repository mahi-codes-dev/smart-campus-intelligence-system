import logging
logger = logging.getLogger(__name__)
from flask import Blueprint, jsonify, request
from services.readiness_service import calculate_readiness
from auth.auth_middleware import token_required
from services.readiness_service import get_top_students
from services.student_service import get_student_record_by_user_id

readiness_bp = Blueprint("readiness_bp", __name__)


@readiness_bp.route("/readiness/<int:student_id>", methods=["GET"])
@token_required
def get_readiness(student_id):
    try:
        if request.user.get("role_id") == 3:
            student = get_student_record_by_user_id(request.user["user_id"])
            if not student or student["id"] != student_id:
                return jsonify({"error": "Students can only view their own readiness"}), 403

        result = calculate_readiness(student_id)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500
    

@readiness_bp.route("/top-students", methods=["GET"])
@token_required
def top_students():
    try:
        data = get_top_students()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500
