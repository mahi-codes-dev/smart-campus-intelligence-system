"""
User Profile Routes - Handle user profile view and editing
"""
from flask import Blueprint, request, jsonify
from database import get_db_connection
from auth.auth_middleware import token_required
import bcrypt

profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')


@profile_bp.route('/me', methods=['GET'])
@token_required
def get_profile(current_user):
    """Get current user's profile"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        user_id = current_user['id']
        user_role = current_user['role']
        table_name = f"{user_role.lower()}s"
        
        # Fetch user info based on role
        if user_role == 'Student':
            cur.execute('''
                SELECT s.id, s.name, s.email, s.roll_number, s.cgpa, s.created_at,
                       d.department_name,
                       COALESCE(
                           ROUND(100.0 * SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / 
                           NULLIF(COUNT(DISTINCT a.id), 0), 2), 0
                       ) as attendance
                FROM students s
                LEFT JOIN departments d ON s.department_id = d.id
                LEFT JOIN attendance a ON s.id = a.student_id
                WHERE s.id = %s
                GROUP BY s.id, s.name, s.email, s.roll_number, s.cgpa, s.created_at, d.department_name
            ''', (user_id,))
        elif user_role == 'Faculty':
            cur.execute('''
                SELECT id, name, email, specialization, phone, created_at
                FROM faculty WHERE id = %s
            ''', (user_id,))
        else:  # Admin
            cur.execute('''
                SELECT id, name, email, phone, created_at
                FROM admin_users WHERE id = %s
            ''', (user_id,))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result:
            return jsonify({'error': 'User not found'}), 404
        
        # Format response based on role
        if user_role == 'Student':
            profile_data = {
                'id': result[0],
                'name': result[1],
                'email': result[2],
                'roll_number': result[3],
                'cgpa': result[4],
                'created_at': result[5].isoformat() if result[5] else None,
                'department': result[6],
                'attendance': result[7],
                'role': 'Student'
            }
        elif user_role == 'Faculty':
            profile_data = {
                'id': result[0],
                'name': result[1],
                'email': result[2],
                'specialization': result[3],
                'phone': result[4],
                'created_at': result[5].isoformat() if result[5] else None,
                'role': 'Faculty'
            }
        else:  # Admin
            profile_data = {
                'id': result[0],
                'name': result[1],
                'email': result[2],
                'phone': result[3],
                'created_at': result[4].isoformat() if result[4] else None,
                'role': 'Admin'
            }
        
        return jsonify(profile_data), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@profile_bp.route('/update', methods=['PUT'])
@token_required
def update_profile(current_user):
    """
    Update user profile
    
    Request body:
    {
        "name": "John Doe",
        "phone": "1234567890",
        "specialization": "Computer Science" (for faculty)
    }
    """
    data = request.get_json()
    user_id = current_user['id']
    user_role = current_user['role']
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Update based on role
        if user_role == 'Student':
            allowed_fields = ['name']
            updates = []
            params = []
            
            if 'name' in data:
                updates.append('name = %s')
                params.append(data['name'])
            
            if updates:
                params.append(user_id)
                cur.execute(f"UPDATE students SET {', '.join(updates)} WHERE id = %s", params)
        
        elif user_role == 'Faculty':
            allowed_fields = ['name', 'phone', 'specialization']
            updates = []
            params = []
            
            for field in allowed_fields:
                if field in data:
                    updates.append(f"{field} = %s")
                    params.append(data[field])
            
            if updates:
                params.append(user_id)
                cur.execute(f"UPDATE faculty SET {', '.join(updates)} WHERE id = %s", params)
        
        else:  # Admin
            allowed_fields = ['name', 'phone']
            updates = []
            params = []
            
            for field in allowed_fields:
                if field in data:
                    updates.append(f"{field} = %s")
                    params.append(data[field])
            
            if updates:
                params.append(user_id)
                cur.execute(f"UPDATE admin_users SET {', '.join(updates)} WHERE id = %s", params)
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'status': 'success'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@profile_bp.route('/<int:user_id>', methods=['GET'])
@token_required
def get_user_profile(current_user, user_id):
    """
    Get profile of a specific user (Admin/Faculty can view students)
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check permissions
        if current_user['role'] == 'Student' and current_user['id'] != user_id:
            return jsonify({'error': 'You can only view your own profile'}), 403
        
        # Fetch student profile
        cur.execute('''
            SELECT s.id, s.name, s.email, s.roll_number, s.cgpa, s.created_at,
                   d.department_name,
                   COALESCE(
                       ROUND(100.0 * SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / 
                       NULLIF(COUNT(DISTINCT a.id), 0), 2), 0
                   ) as attendance
            FROM students s
            LEFT JOIN departments d ON s.department_id = d.id
            LEFT JOIN attendance a ON s.id = a.student_id
            WHERE s.id = %s
            GROUP BY s.id, s.name, s.email, s.roll_number, s.cgpa, s.created_at, d.department_name
        ''', (user_id,))
        
        result = cur.fetchone()
        
        if not result:
            return jsonify({'error': 'User not found'}), 404
        
        profile_data = {
            'id': result[0],
            'name': result[1],
            'email': result[2],
            'roll_number': result[3],
            'cgpa': result[4],
            'created_at': result[5].isoformat() if result[5] else None,
            'department': result[6],
            'attendance': result[7],
            'role': 'Student'
        }
        
        # Fetch readiness score
        cur.execute('''
            SELECT score, risk_level, placement_outlook, created_at
            FROM readiness_scores WHERE student_id = %s
            ORDER BY created_at DESC LIMIT 1
        ''', (user_id,))
        
        readiness = cur.fetchone()
        if readiness:
            profile_data['readiness'] = {
                'score': readiness[0],
                'risk_level': readiness[1],
                'placement_outlook': readiness[2],
                'updated_at': readiness[3].isoformat() if readiness[3] else None
            }
        
        # Fetch recent marks
        cur.execute('''
            SELECT s.name, m.marks, m.percentage, m.grade, m.created_at
            FROM marks m
            JOIN subjects s ON m.subject_id = s.id
            WHERE m.student_id = %s
            ORDER BY m.created_at DESC
            LIMIT 5
        ''', (user_id,))
        
        marks = []
        for row in cur.fetchall():
            marks.append({
                'subject': row[0],
                'marks': row[1],
                'percentage': row[2],
                'grade': row[3],
                'date': row[4].isoformat() if row[4] else None
            })
        
        if marks:
            profile_data['recent_marks'] = marks
        
        cur.close()
        conn.close()
        
        return jsonify(profile_data), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@profile_bp.route('/avatar/upload', methods=['POST'])
@token_required
def upload_avatar(current_user):
    """
    Upload profile avatar (placeholder for file upload)
    Note: Actual file storage would require additional setup
    """
    if 'avatar' not in request.files:
        return jsonify({'error': 'No avatar file provided'}), 400
    
    file = request.files['avatar']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if not file.filename or '.' not in file.filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if file_ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        # TODO: Implement actual file storage (AWS S3, local filesystem, etc.)
        return jsonify({
            'message': 'Avatar uploaded successfully (feature in development)',
            'status': 'pending',
            'avatar_url': '/static/default-avatar.png'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@profile_bp.route('/preferences', methods=['GET'])
@token_required
def get_preferences(current_user):
    """Get user preferences (theme, notifications, etc.)"""
    # This would typically fetch from a preferences table
    # For now, returning default preferences
    return jsonify({
        'theme': 'light',  # or 'dark'
        'notifications': {
            'email': True,
            'attendance_alerts': True,
            'marks_updates': True,
            'placement_alerts': True
        },
        'language': 'en',
        'timezone': 'UTC'
    }), 200


@profile_bp.route('/preferences', methods=['PUT'])
@token_required
def update_preferences(current_user):
    """Update user preferences"""
    data = request.get_json()
    
    try:
        # TODO: Implement preference storage in database
        return jsonify({
            'message': 'Preferences updated successfully',
            'status': 'success',
            'preferences': data
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
