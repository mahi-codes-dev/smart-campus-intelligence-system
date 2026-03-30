"""
Password Reset Service - Handle password reset flows
"""
from datetime import datetime, timedelta
from flask import current_app
import jwt
import os
from services.notification_service import NotificationService


class PasswordResetService:
    """Service for password reset functionality"""
    
    RESET_TOKEN_EXPIRY = 3600  # 1 hour in seconds
    
    @staticmethod
    def generate_reset_token(user_email):
        """
        Generate a secure password reset token
        
        Args:
            user_email: User's email address
        
        Returns:
            str: JWT token
        """
        payload = {
            'email': user_email,
            'exp': datetime.utcnow() + timedelta(seconds=PasswordResetService.RESET_TOKEN_EXPIRY),
            'iat': datetime.utcnow(),
            'purpose': 'password_reset'
        }
        
        token = jwt.encode(
            payload,
            current_app.config.get('SECRET_KEY', 'your-secret-key'),
            algorithm='HS256'
        )
        return token
    
    @staticmethod
    def verify_reset_token(token):
        """
        Verify password reset token and extract email
        
        Args:
            token: JWT token
        
        Returns:
            str: Email if valid, None if invalid/expired
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config.get('SECRET_KEY', 'your-secret-key'),
                algorithms=['HS256']
            )
            
            if payload.get('purpose') != 'password_reset':
                return None
            
            return payload.get('email')
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def send_reset_email(email, username, reset_url):
        """
        Send password reset email to user
        
        Args:
            email: User's email
            username: User's name
            reset_url: Full URL for password reset
        
        Returns:
            bool: True if sent successfully
        """
        token = PasswordResetService.generate_reset_token(email)
        reset_link = f"{reset_url}?token={token}"
        
        return NotificationService.send_password_reset_email(
            email,
            reset_link,
            username
        )
    
    @staticmethod
    def is_strong_password(password):
        """
        Validate password strength
        
        Args:
            password: Password to validate
        
        Returns:
            tuple: (bool: is_valid, str: error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(char.isupper() for char in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(char.islower() for char in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(char.isdigit() for char in password):
            return False, "Password must contain at least one digit"
        
        if not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?' for char in password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is strong"
