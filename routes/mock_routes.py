from flask import Blueprint, request, jsonify
from services.mock_service import add_mock_test, get_mock_scores
from auth.auth_middleware import token_required, role_required
from utils.response import success_response, error_response
from utils.validators import validate_required_fields

mock_bp = Blueprint("mock_bp", __name__)


# Add mock test (Faculty only)
@mock_bp.route("/mock-tests", methods=["POST"])
@token_required
@role_required("Faculty")
def create_mock():
    try:
        data = request.get_json()

        # ✅ Validation
        valid, error = validate_required_fields(data, ["student_id", "score", "test_name"])
        if not valid:
            return error_response(error)

        student_id = data["student_id"]
        score = data["score"]
        test_name = data["test_name"]

        add_mock_test(student_id, score, test_name)

        return success_response(
            data = {
                "student_id": student_id,
                "score": score,
                "test_name": test_name
            },
            message="Mock test added", status=201
        )

    except Exception as e:
        return error_response(str(e), 500)


# Get mock tests for student
@mock_bp.route("/mock-tests/<int:student_id>", methods=["GET"])
@token_required
def fetch_mock(student_id):
    try:
        data = get_mock_scores(student_id)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500