from flask import Blueprint, jsonify
from services.student_service import fetch_all_students

student_bp = Blueprint("student_bp", __name__)

@student_bp.route("/students")
def get_students():
    try:
        students = fetch_all_students()
        return jsonify(students), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500