"""
Real-time Notification Service - WebSocket and polling-based notifications
Handles notification creation, delivery, and status management
"""
import psycopg2
from datetime import datetime, timedelta
from database import get_db_connection
import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class RealtimeNotificationService:
    """Service for managing real-time notifications"""

    # Notification types
    TYPE_ACADEMIC = "academic"
    TYPE_SYSTEM = "system"
    TYPE_ALERT = "alert"
    TYPE_ASSIGNMENT = "assignment"
    TYPE_RESULT = "result"
    TYPE_ATTENDANCE = "attendance"

    # Priority levels
    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_URGENT = "urgent"

    @staticmethod
    def ensure_notifications_table():
        """Create notifications table if it doesn't exist"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    type VARCHAR(50) DEFAULT 'system',
                    priority VARCHAR(20) DEFAULT 'medium',
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    metadata JSONB DEFAULT '{}',
                    action_url VARCHAR(500),
                    CONSTRAINT valid_type CHECK (type IN ('academic', 'system', 'alert', 'assignment', 'result', 'attendance')),
                    CONSTRAINT valid_priority CHECK (priority IN ('low', 'medium', 'high', 'urgent'))
                );

                CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
                CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
                CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
            """)

            conn.commit()
            cur.close()
            conn.close()
            logger.info("Notifications table ensured")
        except Exception as e:
            logger.error(f"Error ensuring notifications table: {str(e)}")
            raise

    @staticmethod
    def create_notification(
        user_id: int,
        title: str,
        message: str,
        notification_type: str = TYPE_SYSTEM,
        priority: str = PRIORITY_MEDIUM,
        action_url: Optional[str] = None,
        metadata: Optional[Dict] = None,
        expires_in_days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new notification

        Args:
            user_id: User ID
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            action_url: Optional URL to navigate to
            metadata: Optional JSON metadata
            expires_in_days: Days until notification expires

        Returns:
            Created notification dict or None if failed
        """
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            expires_at = datetime.now() + timedelta(days=expires_in_days)
            metadata = metadata or {}

            cur.execute("""
                INSERT INTO notifications 
                (user_id, title, message, type, priority, action_url, metadata, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, user_id, title, message, type, priority, is_read, created_at, action_url
            """, (user_id, title, message, notification_type, priority, action_url, str(metadata), expires_at))

            notification = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()

            if notification:
                return {
                    "id": notification[0],
                    "user_id": notification[1],
                    "title": notification[2],
                    "message": notification[3],
                    "type": notification[4],
                    "priority": notification[5],
                    "is_read": notification[6],
                    "created_at": notification[7].isoformat(),
                    "action_url": notification[8]
                }

        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")

        return None

    @staticmethod
    def create_bulk_notifications(
        user_ids: List[int],
        title: str,
        message: str,
        notification_type: str = TYPE_SYSTEM,
        priority: str = PRIORITY_MEDIUM,
        action_url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Create notifications for multiple users

        Args:
            user_ids: List of user IDs
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            action_url: Optional URL
            metadata: Optional JSON metadata

        Returns:
            Number of notifications created
        """
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            expires_at = datetime.now() + timedelta(days=30)
            metadata = metadata or {}

            values_list = []
            for uid in user_ids:
                action_url_val = f"'{action_url}'" if action_url else 'NULL'
                values_list.append(
                    f"({uid}, '{title}', '{message}', '{notification_type}', '{priority}', {action_url_val}, '{metadata}', '{expires_at}')"
                )
            
            values = ",".join(values_list)

            cur.execute(f"""
                INSERT INTO notifications 
                (user_id, title, message, type, priority, action_url, metadata, expires_at)
                VALUES {values}
            """)

            count = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"Created {count} notifications for {len(user_ids)} users")
            return count

        except Exception as e:
            logger.error(f"Error creating bulk notifications: {str(e)}")
            return 0

    @staticmethod
    def get_user_notifications(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        notification_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user notifications

        Args:
            user_id: User ID
            limit: Limit number of notifications
            offset: Pagination offset
            unread_only: Only unread notifications
            notification_type: Filter by type

        Returns:
            List of notifications
        """
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            query = """
                SELECT id, user_id, title, message, type, priority, is_read, created_at, 
                       read_at, action_url
                FROM notifications
                WHERE user_id = %s
            """
            params: List[Any] = [user_id]

            if unread_only:
                query += " AND is_read = FALSE"

            if notification_type:
                query += " AND type = %s"
                params.append(str(notification_type))

            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cur.execute(query, params)
            notifications = cur.fetchall()
            cur.close()
            conn.close()

            return [{
                "id": n[0],
                "user_id": n[1],
                "title": n[2],
                "message": n[3],
                "type": n[4],
                "priority": n[5],
                "is_read": n[6],
                "created_at": n[7].isoformat(),
                "read_at": n[8].isoformat() if n[8] else None,
                "action_url": n[9]
            } for n in notifications]

        except Exception as e:
            logger.error(f"Error getting user notifications: {str(e)}")
            return []

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        """Get count of unread notifications for user"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE",
                (user_id,)
            )
            result = cur.fetchone()
            count = result[0] if result else 0
            cur.close()
            conn.close()

            return count

        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0

    @staticmethod
    def mark_as_read(notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE notifications
                SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s
            """, (notification_id, user_id))

            result = cur.rowcount > 0
            conn.commit()
            cur.close()
            conn.close()

            return result

        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return False

    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        """Mark all user notifications as read"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE notifications
                SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND is_read = FALSE
            """, (user_id,))

            count = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            return count

        except Exception as e:
            logger.error(f"Error marking all as read: {str(e)}")
            return 0

    @staticmethod
    def delete_notification(notification_id: int, user_id: int) -> bool:
        """Delete a notification"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                "DELETE FROM notifications WHERE id = %s AND user_id = %s",
                (notification_id, user_id)
            )

            result = cur.rowcount > 0
            conn.commit()
            cur.close()
            conn.close()

            return result

        except Exception as e:
            logger.error(f"Error deleting notification: {str(e)}")
            return False

    @staticmethod
    def clear_expired_notifications() -> int:
        """Clear expired notifications (older than expiry date)"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                DELETE FROM notifications
                WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
            """)

            count = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"Cleared {count} expired notifications")
            return count

        except Exception as e:
            logger.error(f"Error clearing expired notifications: {str(e)}")
            return 0

    @staticmethod
    def get_notification_statistics(user_id: int) -> Dict[str, Any]:
        """Get notification statistics for user"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Total notifications
            cur.execute(
                "SELECT COUNT(*) FROM notifications WHERE user_id = %s",
                (user_id,)
            )
            result = cur.fetchone()
            total = result[0] if result else 0

            # Unread count
            cur.execute(
                "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE",
                (user_id,)
            )
            result = cur.fetchone()
            unread = result[0] if result else 0

            # By type
            cur.execute("""
                SELECT type, COUNT(*) as count
                FROM notifications
                WHERE user_id = %s
                GROUP BY type
            """, (user_id,))
            by_type = {row[0]: row[1] for row in cur.fetchall()}

            # By priority
            cur.execute("""
                SELECT priority, COUNT(*) as count
                FROM notifications
                WHERE user_id = %s
                GROUP BY priority
            """, (user_id,))
            by_priority = {row[0]: row[1] for row in cur.fetchall()}

            # Urgent unread
            cur.execute(
                "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE AND priority = 'urgent'",
                (user_id,)
            )
            result = cur.fetchone()
            urgent_unread = result[0] if result else 0

            cur.close()
            conn.close()

            return {
                "total": total,
                "unread": unread,
                "urgent_unread": urgent_unread,
                "by_type": by_type,
                "by_priority": by_priority
            }

        except Exception as e:
            logger.error(f"Error getting notification statistics: {str(e)}")
            return {}

    @staticmethod
    def notify_low_attendance(student_id: int, attendance_percentage: float, subject_name: str):
        """Create notification for low attendance"""
        message = f"Your attendance in {subject_name} is {attendance_percentage:.1f}%. Please attend more classes."
        RealtimeNotificationService.create_notification(
            student_id,
            "Low Attendance Alert",
            message,
            notification_type=RealtimeNotificationService.TYPE_ATTENDANCE,
            priority=RealtimeNotificationService.PRIORITY_HIGH,
            action_url="/attendance"
        )

    @staticmethod
    def notify_exam_scheduled(student_id: int, exam_name: str, exam_date: str):
        """Create notification for scheduled exam"""
        message = f"{exam_name} is scheduled on {exam_date}. Please prepare well."
        RealtimeNotificationService.create_notification(
            student_id,
            "Exam Scheduled",
            message,
            notification_type=RealtimeNotificationService.TYPE_ASSIGNMENT,
            priority=RealtimeNotificationService.PRIORITY_MEDIUM,
            action_url="/marks"
        )

    @staticmethod
    def notify_result_published(student_id: int, subject_name: str, marks: float):
        """Create notification for result publication"""
        message = f"Results for {subject_name} have been published. Your marks: {marks}"
        RealtimeNotificationService.create_notification(
            student_id,
            "Result Published",
            message,
            notification_type=RealtimeNotificationService.TYPE_RESULT,
            priority=RealtimeNotificationService.PRIORITY_MEDIUM,
            action_url="/marks"
        )

    @staticmethod
    def notify_at_risk(student_id: int, cgpa: float):
        """Create notification for at-risk student"""
        message = f"Your CGPA has dropped to {cgpa}. Please meet your academic advisor."
        RealtimeNotificationService.create_notification(
            student_id,
            "Academic Performance Alert",
            message,
            notification_type=RealtimeNotificationService.TYPE_ALERT,
            priority=RealtimeNotificationService.PRIORITY_URGENT,
            action_url="/profile"
        )

    @staticmethod
    def notify_faculty_grades_pending(faculty_id: int, subject_code: str, pending_count: int):
        """Create notification for faculty with pending grades"""
        message = f"You have {pending_count} pending grades in {subject_code}. Please submit them."
        RealtimeNotificationService.create_notification(
            faculty_id,
            "Pending Grades",
            message,
            notification_type=RealtimeNotificationService.TYPE_ALERT,
            priority=RealtimeNotificationService.PRIORITY_HIGH,
            action_url="/faculty/marks"
        )

    @staticmethod
    def notify_admin_bulk_import_complete(admin_id: int, import_type: str, success_count: int, error_count: int):
        """Create notification for admin after bulk import"""
        message = f"Bulk {import_type} import completed. Success: {success_count}, Errors: {error_count}"
        RealtimeNotificationService.create_notification(
            admin_id,
            f"Bulk Import Complete",
            message,
            notification_type=RealtimeNotificationService.TYPE_SYSTEM,
            priority=RealtimeNotificationService.PRIORITY_MEDIUM,
            action_url="/admin-dashboard"
        )

