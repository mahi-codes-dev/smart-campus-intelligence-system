from flask import Blueprint, jsonify
from services.prediction_service import predict_placement_from_score
from services.student_dashboard_service import get_student_dashboard_data
from auth.auth_middleware import token_required

prediction_bp = Blueprint("prediction_bp", __name__)


@prediction_bp.route("/predict/<int:student_id>", methods=["GET"])
@token_required
def predict(student_id):
    try:
        data = get_student_dashboard_data(student_id)
        result = predict_placement_from_score(student_id, data["final_score"])
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500