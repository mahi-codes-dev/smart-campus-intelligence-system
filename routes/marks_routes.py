from flask import Blueprint, request, jsonify
from services.marks_service import add_marks, get_marks
from auth.auth_middleware import token_required, role_required

marks_bp = Blueprint("marks_bp", __name__)


@marks_bp.route("/marks", methods=["POST"])
@token_required
@role_required("Faculty")
def create_marks():
    try:
        data = request.get_json()

        student_id = data["student_id"]
        subject_id = data["subject_id"]
        marks_value = data["marks"]
        exam_type = data["exam_type"]

        add_marks(student_id, subject_id, marks_value, exam_type)

        return jsonify({"message": "Marks added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@marks_bp.route("/marks", methods=["GET"])
@token_required
def fetch_marks():
    try:
        data = get_marks()
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500