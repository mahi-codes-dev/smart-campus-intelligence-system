"""
Password Reset Routes - Handle password reset workflow
"""
from flask import Blueprint, request, jsonify
from database import get_db_connection
from services.password_reset_service import PasswordResetService
from services.notification_service import NotificationService
from auth.auth_middleware import token_required
import bcrypt

password_reset_bp = Blueprint('password_reset', __name__, url_prefix='/api/password')


@password_reset_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Request password reset
    
    Request body:
    {
        "email": "student@example.com"
    }
    """
    data = request.get_json()
    email = data.get('email', '').strip()
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if user exists
        cur.execute('SELECT id, name FROM students WHERE email = %s', (email,))
        user = cur.fetchone()
        
        if not user:
            cur.execute('SELECT id, name FROM faculty WHERE email = %s', (email,))
            user = cur.fetchone()
        
        if not user:
            cur.execute('SELECT id, name FROM admin_users WHERE email = %s', (email,))
            user = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not user:
            # Don't reveal if email exists (security)
            return jsonify({
                'message': 'If email exists, password reset link will be sent',
                'status': 'pending'
            }), 200
        
        # Send reset email
        username = user[1]
        reset_url = f"{request.host_url.rstrip('/')}reset-password"
        
        success = PasswordResetService.send_reset_email(email, username, reset_url)
        
        if success:
            return jsonify({
                'message': 'Password reset link sent to your email',
                'status': 'sent'
            }), 200
        else:
            return jsonify({
                'error': 'Failed to send reset email. Please try again.',
                'status': 'error'
            }), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@password_reset_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Reset password using token
    
    Request body:
    {
        "token": "jwt_token",
        "new_password": "NewPassword123!"
    }
    """
    data = request.get_json()
    token = data.get('token', '').strip()
    new_password = data.get('new_password', '').strip()
    
    if not token or not new_password:
        return jsonify({'error': 'Token and new password are required'}), 400
    
    # Validate password strength
    is_strong, message = PasswordResetService.is_strong_password(new_password)
    if not is_strong:
        return jsonify({'error': message, 'status': 'weak_password'}), 400
    
    # Verify token
    email = PasswordResetService.verify_reset_token(token)
    if not email:
        return jsonify({'error': 'Invalid or expired reset token'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Update password in students table
        cur.execute(
            'UPDATE students SET password = %s WHERE email = %s',
            (hashed_password.decode('utf-8'), email)
        )
        
        # Update password in faculty table
        cur.execute(
            'UPDATE faculty SET password = %s WHERE email = %s',
            (hashed_password.decode('utf-8'), email)
        )
        
        # Update password in admin_users table
        cur.execute(
            'UPDATE admin_users SET password = %s WHERE email = %s',
            (hashed_password.decode('utf-8'), email)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'message': 'Password reset successfully',
            'status': 'success'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@password_reset_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """
    Change password for logged-in user
    
    Request body:
    {
        "old_password": "CurrentPassword123!",
        "new_password": "NewPassword456!"
    }
    """
    data = request.get_json()
    old_password = data.get('old_password', '').strip()
    new_password = data.get('new_password', '').strip()
    
    if not old_password or not new_password:
        return jsonify({'error': 'Old and new password are required'}), 400
    
    if old_password == new_password:
        return jsonify({'error': 'New password must be different from old password'}), 400
    
    # Validate new password strength
    is_strong, message = PasswordResetService.is_strong_password(new_password)
    if not is_strong:
        return jsonify({'error': message}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get user's table and current password hash
        user_id = current_user['id']
        user_role = current_user['role']
        
        table_name = f"{user_role.lower()}s"
        cur.execute(f'SELECT password FROM {table_name} WHERE id = %s', (user_id,))
        result = cur.fetchone()
        
        if not result:
            return jsonify({'error': 'User not found'}), 404
        
        current_hash = result[0]
        
        # Verify old password
        if not bcrypt.checkpw(old_password.encode('utf-8'), current_hash.encode('utf-8')):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update to new password
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        cur.execute(
            f'UPDATE {table_name} SET password = %s WHERE id = %s',
            (new_hash.decode('utf-8'), user_id)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'message': 'Password changed successfully',
            'status': 'success'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@password_reset_bp.route('/validate-token', methods=['POST'])
def validate_token():
    """Validate password reset token"""
    data = request.get_json()
    token = data.get('token', '').strip()
    
    if not token:
        return jsonify({'error': 'Token is required'}), 400
    
    email = PasswordResetService.verify_reset_token(token)
    
    if email:
        return jsonify({
            'valid': True,
            'email': email,
            'message': 'Token is valid'
        }), 200
    else:
        return jsonify({
            'valid': False,
            'message': 'Token is invalid or expired'
        }), 400
