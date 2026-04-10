from flask import Blueprint, request, jsonify
from services.marks_service import add_marks, get_marks, save_marks
from auth.auth_middleware_replacement import token_required, role_required
from utils.validators import RequestValidator
from utils.validators import RequestValidator

marks_bp = Blueprint("marks_bp", __name__)


@marks_bp.route("/marks", methods=["POST"])
@token_required
@role_required("Faculty")
def create_marks():
    try:
        v = RequestValidator(request.get_json())
        v.required("student_id", "subject_id", "marks").integer("student_id").integer("subject_id").integer("marks", min_val=0, max_val=100)
        if v.has_errors():
            return jsonify({"error": v.first_error()}), 400
        student_id = v.validated_data["student_id"]
        subject_id = v.validated_data["subject_id"]
        marks_value = v.validated_data["marks"]
        exam_type = v.data.get("exam_type")

        add_marks(student_id, subject_id, marks_value, exam_type)

        return jsonify({"message": "Marks added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@marks_bp.route("/marks", methods=["PUT"])
@token_required
@role_required("Faculty")
def update_marks():
    try:
        v = RequestValidator(request.get_json())
        v.required("student_id", "subject_id", "marks").integer("student_id").integer("subject_id").integer("marks", min_val=0, max_val=100)
        if v.has_errors():
            return jsonify({"error": v.first_error()}), 400
        action = save_marks(
            v.validated_data["student_id"],
            v.validated_data["subject_id"],
            v.validated_data["marks"],
            v.data.get("exam_type"),
        )

        return jsonify({
            "message": "Marks updated successfully" if action == "updated" else "Marks saved successfully"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@marks_bp.route("/marks", methods=["GET"])
@token_required
def fetch_marks():
    try:
        user = request.user
        if not user or user.get("role_id") not in (1, 2):
            return jsonify({"error": "Access denied"}), 403

        data = get_marks()
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
