from flask import Blueprint, request, jsonify
from services.mock_service import add_mock_test, get_mock_scores
from auth.auth_middleware import token_required, role_required

mock_bp = Blueprint("mock_bp", __name__)


@mock_bp.route("/mock-tests", methods=["POST"])
@token_required
@role_required("Faculty")
def create_mock():
    try:
        data = request.get_json()

        student_id = data["student_id"]
        score = data["score"]
        test_name = data["test_name"]

        add_mock_test(student_id, score, test_name)

        return jsonify({"message": "Mock test added"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@mock_bp.route("/mock-tests/<int:student_id>", methods=["GET"])
@token_required
def fetch_mock(student_id):
    try:
        data = get_mock_scores(student_id)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500