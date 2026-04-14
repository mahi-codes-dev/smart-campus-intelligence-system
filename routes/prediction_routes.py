import logging
logger = logging.getLogger(__name__)
from flask import Blueprint, jsonify, request
from services.prediction_service import predict_placement_from_score
from services.student_dashboard_service import get_student_dashboard_data
from auth.auth_middleware import token_required
from services.student_service import get_student_record_by_user_id

prediction_bp = Blueprint("prediction_bp", __name__)


@prediction_bp.route("/predict/<int:student_id>", methods=["GET"])
@token_required
def predict(student_id):
    try:
        if request.user.get("role_id") == 3:
            student = get_student_record_by_user_id(request.user["user_id"])
            if not student or student["id"] != student_id:
                return jsonify({"error": "Students can only view their own prediction"}), 403

        data = get_student_dashboard_data(student_id)

        result = predict_placement_from_score(
            student_id,
            data["readiness_score"],
            metrics={
                "attendance": data.get("attendance", 0),
                "marks": data.get("marks", 0),
                "mock_score": data.get("mock_score", 0),
                "skills_score": data.get("skills_score", 0),
            },
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500
