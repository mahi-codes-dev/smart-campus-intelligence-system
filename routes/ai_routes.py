import logging
from flask import Blueprint, jsonify, request, g
from auth.auth_middleware import token_required, role_required
from services.ai_service import AIService
from services.student_service import get_student_record_by_user_id

ai_bp = Blueprint("ai", __name__)
logger = logging.getLogger(__name__)

_MAX_LEN = 1000


@ai_bp.route("/ai/chat/student", methods=["POST"])
@token_required
def student_chat():
    data = request.get_json() or {}
    message = str(data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message is required"}), 400
    if len(message) > _MAX_LEN:
        return jsonify({"error": f"Message too long (max {_MAX_LEN} chars)"}), 400

    student = get_student_record_by_user_id(g.user_id)
    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    try:
        response = AIService.get_student_advice(student["id"], message)
        return jsonify({"response": response}), 200
    except Exception as e:
        logger.exception("student_chat failed")
        return jsonify({"error": "AI service unavailable. Please try again later."}), 503


@ai_bp.route("/ai/chat/faculty", methods=["POST"])
@token_required
@role_required("Faculty", "Admin")
def faculty_chat():
    data = request.get_json() or {}
    query = str(data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Query is required"}), 400
    if len(query) > _MAX_LEN:
        return jsonify({"error": f"Query too long (max {_MAX_LEN} chars)"}), 400

    try:
        from services.faculty_dashboard_service import get_faculty_dashboard_summary
        # Call with no filters so AI always gets full class picture
        summary = get_faculty_dashboard_summary()
        faculty_name = getattr(g, "user_name", None) or "Faculty"
        response = AIService.get_faculty_insights(faculty_name, summary, query)
        return jsonify({"response": response}), 200
    except Exception as e:
        logger.exception("faculty_chat failed")
        return jsonify({"error": "AI service unavailable. Please try again later."}), 503
