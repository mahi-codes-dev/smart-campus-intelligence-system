from flask import Blueprint, jsonify, request, g
from auth.auth_middleware import login_required
from services.ai_service import AIService
from services.student_service import get_student_record_by_user_id

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/ai/chat/student', methods=['POST'])
@login_required
def student_chat():
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
        
    student = get_student_record_by_user_id(g.user_id)
    if not student:
        return jsonify({"error": "Student profile not found"}), 404
        
    response = AIService.get_student_advice(student['id'], message)
    return jsonify({"response": response})

@ai_bp.route('/ai/chat/faculty', methods=['POST'])
@login_required
def faculty_chat():
    data = request.get_json()
    query = data.get('query')
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
        
    # For faculty, we might need to pass class summary data from the faculty dashboard service
    from services.faculty_dashboard_service import get_faculty_dashboard_summary
    summary = get_faculty_dashboard_summary()
    
    response = AIService.get_faculty_insights(g.user_name, summary, query)
    return jsonify({"response": response})
