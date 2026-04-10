from flask import Blueprint, jsonify, g
from auth.auth_middleware import token_required
from services.peer_learning_service import get_peer_mentorship_suggestions, get_mentor_dashboard_stats

peer_learning_bp = Blueprint('peer_learning', __name__)

@peer_learning_bp.route('/peer-learning/suggestions', methods=['GET'])
@token_required
def suggestions():
    """
    Get mentorship suggestions for the logged-in student.
    """
    # Assuming g.user_id is set by token_required and refers to the USER record.
    # We need the STUDENT id.
    from services.student_service import get_student_record_by_user_id
    student = get_student_record_by_user_id(g.user_id)
    
    if not student:
        return jsonify({"error": "Student profile not found"}), 404
        
    suggestions = get_peer_mentorship_suggestions(student['id'])
    return jsonify(suggestions)

@peer_learning_bp.route('/peer-learning/mentor-status', methods=['GET'])
@token_required
def mentor_status():
    """
    Check if the logged-in student is a mentor for any subjects.
    """
    from services.student_service import get_student_record_by_user_id
    student = get_student_record_by_user_id(g.user_id)
    
    if not student:
        return jsonify({"error": "Student profile not found"}), 404
        
    mentor_for = get_mentor_dashboard_stats(student['id'])
    return jsonify({
        "is_mentor": len(mentor_for) > 0,
        "subjects": mentor_for
    })
