"""
Notification Service - Handles email, SMS, and in-app notifications
"""
from flask_mail import Mail, Message
from flask import current_app
from datetime import datetime
import os

mail = Mail()

class NotificationService:
    """Service for sending notifications across multiple channels"""
    
    @staticmethod
    def init_mail(app):
        """Initialize Flask-Mail with app config"""
        mail.init_app(app)
    
    @staticmethod
    def send_email(to_email, subject, body, html=None, attachments=None):
        """
        Send email notification
        
        Args:
            to_email: Recipient email address (string or list)
            subject: Email subject
            body: Plain text body
            html: HTML body (optional)
            attachments: List of file paths to attach
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if isinstance(to_email, str):
                to_email = [to_email]
            
            msg = Message(
                subject=subject,
                recipients=list(to_email) if isinstance(to_email, (list, tuple)) else [to_email],
                body=body,
                html=html,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@campus.edu')
            )
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            msg.attach(
                                filename=os.path.basename(file_path),
                                content_type="application/octet-stream",
                                data=attachment.read()
                            )
            
            mail.send(msg)
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    @staticmethod
    def send_attendance_alert(student_email, student_name, attendance_percentage, threshold=75):
        """Send low attendance warning"""
        if attendance_percentage < threshold:
            subject = f"⚠️ Attendance Alert - Action Required"
            body = f"""
Dear {student_name},

Your current attendance is {attendance_percentage}%, which is below the required threshold of {threshold}%.

Please ensure regular attendance to avoid academic consequences.

Regards,
Smart Campus System
            """
            html = f"""
<html>
  <body style="font-family: Arial, sans-serif;">
    <h2>Attendance Alert</h2>
    <p>Dear <strong>{student_name}</strong>,</p>
    <p>Your current attendance is <span style="color: red; font-weight: bold;">{attendance_percentage}%</span>, 
       which is below the required threshold of {threshold}%.</p>
    <p>Please ensure regular attendance to avoid academic consequences.</p>
    <hr>
    <p><em>Smart Campus Intelligence System</em></p>
  </body>
</html>
            """
            return NotificationService.send_email(student_email, subject, body, html)
        return False
    
    @staticmethod
    def send_marks_alert(student_email, student_name, subject_name, marks, percentage):
        """Send poor marks alert"""
        subject_line = f"📊 Marks Update - {subject_name}"
        body = f"""
Dear {student_name},

Your marks for {subject_name} have been updated:
Score: {marks} ({percentage}%)

Keep working hard to improve your performance!

Regards,
Smart Campus System
        """
        html = f"""
<html>
  <body style="font-family: Arial, sans-serif;">
    <h2>Marks Update</h2>
    <p>Dear <strong>{student_name}</strong>,</p>
    <p>Your marks for <strong>{subject_name}</strong> have been updated:</p>
    <p style="font-size: 18px; color: {'green' if percentage >= 70 else 'orange'if percentage >= 50 else 'red'};">
      <strong>Score: {marks} ({percentage}%)</strong>
    </p>
    <p>Keep working hard to improve your performance!</p>
    <hr>
    <p><em>Smart Campus Intelligence System</em></p>
  </body>
</html>
        """
        return NotificationService.send_email(student_email, subject_line, body, html)
    
    @staticmethod
    def send_placement_readiness_alert(student_email, student_name, readiness_score, risk_level):
        """Send placement readiness update"""
        subject_line = f"🎯 Placement Readiness Update"
        color = 'green' if risk_level == 'Low Risk' else 'orange' if risk_level == 'Medium Risk' else 'red'
        
        body = f"""
Dear {student_name},

Your current placement readiness score is {readiness_score}/100.
Risk Level: {risk_level}

Keep improving your skills to enhance your placement prospects!

Regards,
Smart Campus System
        """
        html = f"""
<html>
  <body style="font-family: Arial, sans-serif;">
    <h2>Placement Readiness Update</h2>
    <p>Dear <strong>{student_name}</strong>,</p>
    <p>Your current placement readiness score: <span style="color: {color}; font-weight: bold; font-size: 18px;">{readiness_score}/100</span></p>
    <p>Risk Level: <span style="color: {color}; font-weight: bold;">{risk_level}</span></p>
    <p>Keep improving your skills to enhance your placement prospects!</p>
    <hr>
    <p><em>Smart Campus Intelligence System</em></p>
  </body>
</html>
        """
        return NotificationService.send_email(student_email, subject_line, body, html)
    
    @staticmethod
    def send_mock_test_reminder(student_email, student_name, mock_test_name, date):
        """Send mock test reminder"""
        subject_line = f"📝 Mock Test Reminder - {mock_test_name}"
        body = f"""
Dear {student_name},

This is a reminder that {mock_test_name} is scheduled for {date}.

Please ensure you have prepared well for the test.

Regards,
Smart Campus System
        """
        html = f"""
<html>
  <body style="font-family: Arial, sans-serif;">
    <h2>Mock Test Reminder</h2>
    <p>Dear <strong>{student_name}</strong>,</p>
    <p>This is a reminder that <strong>{mock_test_name}</strong> is scheduled for <strong>{date}</strong>.</p>
    <p>Please ensure you have prepared well for the test.</p>
    <hr>
    <p><em>Smart Campus Intelligence System</em></p>
  </body>
</html>
        """
        return NotificationService.send_email(student_email, subject_line, body, html)
    
    @staticmethod
    def send_password_reset_email(email, reset_link, username):
        """Send password reset confirmation"""
        subject = "Password Reset Request - Smart Campus System"
        body = f"""
Dear {username},

We received a request to reset your password. Click the link below to proceed:
{reset_link}

This link is valid for 1 hour.

If you did not request this, please ignore this email.

Regards,
Smart Campus System
        """
        html = f"""
<html>
  <body style="font-family: Arial, sans-serif;">
    <h2>Password Reset Request</h2>
    <p>Dear <strong>{username}</strong>,</p>
    <p>We received a request to reset your password.</p>
    <p><a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a></p>
    <p>This link is valid for 1 hour.</p>
    <p><small>If you did not request this, please ignore this email.</small></p>
    <hr>
    <p><em>Smart Campus Intelligence System</em></p>
  </body>
</html>
        """
        return NotificationService.send_email(email, subject, body, html)
    
    @staticmethod
    def send_bulk_email(recipients_list, subject, body, html=None):
        """
        Send email to multiple recipients
        
        Args:
            recipients_list: List of email addresses
            subject: Email subject
            body: Plain text body
            html: HTML body (optional)
        
        Returns:
            int: Number of successfully sent emails
        """
        success_count = 0
        for recipient in recipients_list:
            if NotificationService.send_email(recipient, subject, body, html):
                success_count += 1
        return success_count


# Announcement/Notification Model (in-app)
class InAppNotification:
    """In-app notification record"""
    
    def __init__(self, user_id, notification_type, title, message, data=None, is_read=False):
        self.user_id = user_id
        self.notification_type = notification_type  # 'alert', 'announcement', 'reminder', 'message'
        self.title = title
        self.message = message
        self.data = data or {}
        self.is_read = is_read
        self.created_at = datetime.now()
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat()
        }
