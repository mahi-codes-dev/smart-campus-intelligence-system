from flask import Blueprint, jsonify
from services.student_service import fetch_all_students
from auth.auth_middleware import token_required

student_bp = Blueprint("student_bp", __name__)

@student_bp.route("/students")
@token_required
def get_students():
    try:
        students = fetch_all_students()
        return jsonify(students), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500