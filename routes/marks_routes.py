from flask import Blueprint, request, jsonify
from services.marks_service import add_marks, get_marks, save_marks
from auth.auth_middleware import token_required, role_required

marks_bp = Blueprint("marks_bp", __name__)


@marks_bp.route("/marks", methods=["POST"])
@token_required
@role_required("Faculty")
def create_marks():
    try:
        data = request.get_json() or {}
        print("FACULTY_MARKS_CREATE_REQUEST:", data)

        if not all(k in data for k in ("student_id", "subject_id", "marks")):
            return jsonify({"error": "student_id, subject_id, and marks are required"}), 400

        student_id = data["student_id"]
        subject_id = data["subject_id"]
        marks_value = data["marks"]
        exam_type = data.get("exam_type")

        add_marks(student_id, subject_id, marks_value, exam_type)

        return jsonify({"message": "Marks added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@marks_bp.route("/marks", methods=["PUT"])
@token_required
@role_required("Faculty")
def update_marks():
    try:
        data = request.get_json() or {}
        print("FACULTY_MARKS_UPDATE_REQUEST:", data)

        if not all(k in data for k in ("student_id", "subject_id", "marks")):
            return jsonify({"error": "student_id, subject_id, and marks are required"}), 400

        action = save_marks(
            data["student_id"],
            data["subject_id"],
            data["marks"],
            data.get("exam_type"),
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
        if request.user.get("role_id") not in (1, 2):
            return jsonify({"error": "Access denied"}), 403

        data = get_marks()
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
