"""
Recommendation Engine Routes

REST API endpoints for:
- Student performance analysis
- Subject recommendations
- Career guidance
- At-risk prediction
- Learning resources
- Peer collaboration recommendations
"""

import logging
from flask import Blueprint, request, jsonify, g
from services.recommendation_service import RecommendationService
from auth.auth_middleware import token_required

logger = logging.getLogger(__name__)

recommendation_bp = Blueprint("recommendation", __name__, url_prefix="/api/recommendations")


@recommendation_bp.route("/performance/<int:student_id>", methods=["GET"])
@token_required
def get_performance_analysis(student_id: int):
    """
    Get comprehensive student performance analysis

    Query Parameters:
        - None

    Returns:
        Performance metrics, subject performance, skills, attendance
    """
    try:
        # Verify user has access (student viewing own data or admin)
        if g.user_role not in ["Admin", "Faculty"] and g.user_id != student_id:
            return jsonify({"error": "Unauthorized"}), 403

        analysis = RecommendationService.analyze_student_performance(student_id)

        if "error" in analysis:
            return jsonify({"error": analysis["error"]}), 404

        return jsonify(analysis), 200

    except Exception as e:
        logger.error(f"Performance analysis route error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@recommendation_bp.route("/subjects/<int:student_id>", methods=["GET"])
@token_required
def get_subject_recommendations(student_id: int):
    """
    Get subject-specific recommendations for improvement

    Query Parameters:
        - limit: Number of recommendations (default: 5)

    Returns:
        List of subject recommendations with reasoning and priorities
    """
    try:
        # Verify access
        if g.user_role not in ["Admin", "Faculty"] and g.user_id != student_id:
            return jsonify({"error": "Unauthorized"}), 403

        limit = request.args.get("limit", 5, type=int)
        limit = min(limit, 10)  # Cap at 10

        recommendations = RecommendationService.get_subject_recommendations(student_id, limit)

        return jsonify({
            "student_id": student_id,
            "recommendations": recommendations,
            "count": len(recommendations),
        }), 200

    except Exception as e:
        logger.error(f"Subject recommendation route error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@recommendation_bp.route("/career/<int:student_id>", methods=["GET"])
@token_required
def get_career_guidance(student_id: int):
    """
    Get career guidance based on performance and skills

    Query Parameters:
        - None

    Returns:
        Career paths, skill gaps, next steps, and recommendations
    """
    try:
        # Verify access
        if g.user_role not in ["Admin", "Faculty"] and g.user_id != student_id:
            return jsonify({"error": "Unauthorized"}), 403

        career_rec = RecommendationService.get_career_recommendations(student_id)

        if "error" in career_rec:
            return jsonify({"error": career_rec["error"]}), 404

        return jsonify(career_rec), 200

    except Exception as e:
        logger.error(f"Career guidance route error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@recommendation_bp.route("/risk/<int:student_id>", methods=["GET"])
@token_required
def get_at_risk_prediction(student_id: int):
    """
    Get at-risk prediction with intervention recommendations

    Query Parameters:
        - None

    Returns:
        Risk level (Low/Medium/High/Critical), risk factors, interventions
    """
    try:
        # Verify access (Faculty and Admin can access all, students own data)
        if g.user_role not in ["Admin", "Faculty"] and g.user_id != student_id:
            return jsonify({"error": "Unauthorized"}), 403

        prediction = RecommendationService.predict_at_risk_status(student_id)

        if "error" in prediction:
            return jsonify({"error": prediction["error"]}), 404

        return jsonify(prediction), 200

    except Exception as e:
        logger.error(f"At-risk prediction route error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@recommendation_bp.route("/peers/<int:student_id>", methods=["GET"])
@token_required
def get_peer_recommendations(student_id: int):
    """
    Get peer collaboration recommendations

    Query Parameters:
        - limit: Number of peers to recommend (default: 10)

    Returns:
        List of peers with similar performance for collaboration
    """
    try:
        # Verify access
        if g.user_role not in ["Admin", "Faculty"] and g.user_id != student_id:
            return jsonify({"error": "Unauthorized"}), 403

        limit = request.args.get("limit", 10, type=int)
        limit = min(limit, 20)  # Cap at 20

        peers = RecommendationService.get_peer_recommendations(student_id, limit)

        return jsonify({
            "student_id": student_id,
            "peers": peers,
            "count": len(peers),
        }), 200

    except Exception as e:
        logger.error(f"Peer recommendation route error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@recommendation_bp.route("/resources/<int:student_id>", methods=["GET"])
@token_required
def get_learning_resources(student_id: int):
    """
    Get personalized learning resources and study materials

    Query Parameters:
        - subject_id: Optional subject ID for targeted resources

    Returns:
        List of recommended learning resources with links and priorities
    """
    try:
        # Verify access
        if g.user_role not in ["Admin", "Faculty"] and g.user_id != student_id:
            return jsonify({"error": "Unauthorized"}), 403

        subject_id = request.args.get("subject_id", None, type=int)
        resources = RecommendationService.get_learning_resources(student_id, subject_id)

        return jsonify({
            "student_id": student_id,
            "resources": resources,
            "count": len(resources),
        }), 200

    except Exception as e:
        logger.error(f"Learning resources route error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@recommendation_bp.route("/summary/<int:student_id>", methods=["GET"])
@token_required
def get_recommendation_summary(student_id: int):
    """
    Get comprehensive recommendation summary (all data combined)

    Query Parameters:
        - None

    Returns:
        Combined performance, career, risk, and resource recommendations
    """
    try:
        # Verify access
        if g.user_role not in ["Admin", "Faculty"] and g.user_id != student_id:
            return jsonify({"error": "Unauthorized"}), 403

        # Collect all recommendations
        performance = RecommendationService.analyze_student_performance(student_id)
        if "error" in performance:
            return jsonify({"error": performance["error"]}), 404

        career = RecommendationService.get_career_recommendations(student_id)
        risk = RecommendationService.predict_at_risk_status(student_id)
        resources = RecommendationService.get_learning_resources(student_id)
        peers = RecommendationService.get_peer_recommendations(student_id, 5)
        subjects = RecommendationService.get_subject_recommendations(student_id, 3)

        return jsonify({
            "student_id": student_id,
            "performance_analysis": performance,
            "career_guidance": career,
            "at_risk_assessment": risk,
            "learning_resources": resources,
            "peer_recommendations": peers,
            "subject_recommendations": subjects,
            "summary_timestamp": performance.get("analysis_timestamp"),
        }), 200

    except Exception as e:
        logger.error(f"Recommendation summary route error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@recommendation_bp.route("/batch-risk", methods=["POST"])
@token_required
def batch_at_risk_analysis():
    """
    Batch analyze multiple students for at-risk status (admin only)

    Request Body:
        {
            "student_ids": [1, 2, 3, ...],
            "include_interventions": true
        }

    Returns:
        List of at-risk predictions for multiple students
    """
    try:
        if g.user_role != "Admin":
            return jsonify({"error": "Admin access required"}), 403

        data = request.get_json()
        student_ids = data.get("student_ids", [])

        if not student_ids or not isinstance(student_ids, list):
            return jsonify({"error": "Invalid student_ids"}), 400

        # Limit to 100 students per request
        student_ids = student_ids[:100]

        results = []
        for student_id in student_ids:
            prediction = RecommendationService.predict_at_risk_status(student_id)
            if "error" not in prediction:
                results.append(prediction)

        # Sort by risk score descending
        results.sort(key=lambda x: x.get("risk_score", 0), reverse=True)

        return jsonify({
            "total_analyzed": len(student_ids),
            "at_risk_count": len([r for r in results if r.get("risk_level") in ["Critical", "High"]]),
            "results": results,
        }), 200

    except Exception as e:
        logger.error(f"Batch risk analysis route error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@recommendation_bp.route("/class-insights/<class_id>", methods=["GET"])
@token_required
def get_class_insights(class_id: int):
    """
    Get aggregate insights for an entire class (faculty/admin only)

    Query Parameters:
        - None

    Returns:
        Class-level statistics, at-risk students, average performance
    """
    try:
        if g.user_role not in ["Admin", "Faculty"]:
            return jsonify({"error": "Unauthorized"}), 403

        # Note: This would require a class_students table/mapping
        # For now, returning placeholder
        return jsonify({
            "class_id": class_id,
            "message": "Class insights feature ready for Phase 7",
            "metrics": {
                "total_students": 0,
                "average_marks": 0,
                "attendance_average": 0,
                "at_risk_count": 0,
            },
        }), 200

    except Exception as e:
        logger.error(f"Class insights route error: {str(e)}")
        return jsonify({"error": str(e)}), 500
