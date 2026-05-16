import logging
logger = logging.getLogger(__name__)
from flask import Blueprint, request, jsonify
from services.marks_service import add_marks, get_marks, save_marks
from auth.auth_middleware import token_required, role_required
from utils.validators import RequestValidator
from utils.pagination import PaginationHelper
from utils.schemas import create_error_response

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
        return jsonify({"error": "An internal error occurred"}), 500


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
        return jsonify({"error": "An internal error occurred"}), 500


@marks_bp.route("/marks", methods=["GET"])
@token_required
def fetch_marks():
    try:
        user = request.user
        if not user or user.get("role_id") not in (1, 2):
            return jsonify({"error": "Access denied"}), 403

        # Get pagination parameters
        params, errors = PaginationHelper.get_pagination_params()
        if errors:
            error_resp, status_code = create_error_response("INVALID_PARAMS", "Invalid pagination parameters", 400, errors)
            return jsonify(error_resp), status_code

        # Get all marks
        all_marks = get_marks()
        
        # Apply pagination
        page = params['page']
        per_page = params['per_page']
        total = len(all_marks) if all_marks else 0
        offset = (page - 1) * per_page
        marks = all_marks[offset:offset + per_page] if all_marks else []
        
        response = PaginationHelper.paginate(marks, total, page, per_page)
        return jsonify(response), 200

    except Exception as e:
        logger.exception("fetch_marks failed")
        error_resp, status_code = create_error_response("SERVER_ERROR", "An internal error occurred", 500)
        return jsonify(error_resp), status_code
