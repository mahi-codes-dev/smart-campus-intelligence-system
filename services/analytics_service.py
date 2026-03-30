"""
Analytics Service - Comprehensive data aggregation and metrics calculation
Provides insights into student performance, attendance, and departmental analysis
"""
from database import get_db_connection
from datetime import datetime, timedelta
from statistics import mean, stdev
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for generating analytics and performance metrics"""
    
    @staticmethod
    def get_overall_statistics() -> Dict[str, Any]:
        """
        Get system-wide statistics
        
        Returns:
            dict: Overall stats including totals and averages
        """
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Get total students
            cur.execute("SELECT COUNT(*) FROM students")
            result = cur.fetchone()
            total_students = result[0] if result else 0
            
            # Get average CGPA
            cur.execute("SELECT AVG(CAST(cgpa AS FLOAT)) FROM students WHERE cgpa > 0")
            result = cur.fetchone()
            avg_cgpa = result[0] if result else 0.0
            
            # Get total attendance records
            cur.execute("SELECT COUNT(*) FROM attendance")
            result = cur.fetchone()
            total_attendance = result[0] if result else 0
            
            # Get total marks records
            cur.execute("SELECT COUNT(*) FROM marks")
            result = cur.fetchone()
            total_marks = result[0] if result else 0
            
            # Get average attendance percentage
            cur.execute("""
                SELECT AVG(
                    CAST(
                        (SELECT COUNT(*) FROM attendance a2 
                         WHERE a2.student_id = a1.student_id 
                         AND a2.status = 'Present') 
                        AS FLOAT
                    ) / NULLIF(
                        (SELECT COUNT(*) FROM attendance a3 
                         WHERE a3.student_id = a1.student_id), 0
                    ) * 100
                ) FROM (SELECT DISTINCT student_id FROM attendance) a1
            """)
            result = cur.fetchone()
            avg_attendance = result[0] if result else 0.0
            
            # Get number of departments
            cur.execute("SELECT COUNT(*) FROM departments")
            result = cur.fetchone()
            total_departments = result[0] if result else 0
            
            # Get number of subjects
            cur.execute("SELECT COUNT(*) FROM subjects")
            result = cur.fetchone()
            total_subjects = result[0] if result else 0
            
            return {
                'total_students': int(total_students),
                'avg_cgpa': round(float(avg_cgpa or 0), 2),
                'total_attendance_records': int(total_attendance),
                'total_marks_records': int(total_marks),
                'avg_attendance_percentage': round(float(avg_attendance or 0), 2),
                'total_departments': int(total_departments),
                'total_subjects': int(total_subjects),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching overall statistics: {str(e)}")
            return {'error': str(e)}
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_student_performance_metrics() -> Dict[str, Any]:
        """
        Get performance distribution metrics
        
        Returns:
            dict: Performance distribution and statistics
        """
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Get CGPA distribution
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN cgpa >= 9.0 THEN 'Excellent (9.0-10.0)'
                        WHEN cgpa >= 8.0 THEN 'Very Good (8.0-8.9)'
                        WHEN cgpa >= 7.0 THEN 'Good (7.0-7.9)'
                        WHEN cgpa >= 6.0 THEN 'Average (6.0-6.9)'
                        ELSE 'Below Average (<6.0)'
                    END as category,
                    COUNT(*) as count
                FROM students
                WHERE cgpa > 0
                GROUP BY category
                ORDER BY cgpa DESC
            """)
            
            cgpa_distribution = {}
            for row in cur.fetchall():
                cgpa_distribution[row[0]] = int(row[1])
            
            # Get average marks by exam type
            cur.execute("""
                SELECT exam_type, AVG(CAST(marks AS FLOAT)) as avg_marks, COUNT(*) as count
                FROM marks
                GROUP BY exam_type
                ORDER BY exam_type
            """)
            
            marks_by_exam = {}
            for row in cur.fetchall():
                marks_by_exam[row[0]] = {
                    'average': round(float(row[1] or 0), 2),
                    'count': int(row[2])
                }
            
            # Get top 5 performing students
            cur.execute("""
                SELECT id, name, email, cgpa
                FROM students
                WHERE cgpa > 0
                ORDER BY cgpa DESC
                LIMIT 5
            """)
            
            top_students = []
            for row in cur.fetchall():
                top_students.append({
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'cgpa': round(float(row[3]), 2)
                })
            
            # Get students at risk (CGPA < 6.5)
            cur.execute("""
                SELECT id, name, email, cgpa
                FROM students
                WHERE cgpa > 0 AND cgpa < 6.5
                ORDER BY cgpa ASC
                LIMIT 10
            """)
            
            at_risk_students = []
            for row in cur.fetchall():
                at_risk_students.append({
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'cgpa': round(float(row[3]), 2)
                })
            
            return {
                'cgpa_distribution': cgpa_distribution,
                'marks_by_exam_type': marks_by_exam,
                'top_performers': top_students,
                'at_risk_students': at_risk_students,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching performance metrics: {str(e)}")
            return {'error': str(e)}
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_attendance_analytics() -> Dict[str, Any]:
        """
        Get attendance patterns and analytics
        
        Returns:
            dict: Attendance statistics and trends
        """
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Get attendance status distribution
            cur.execute("""
                SELECT status, COUNT(*) as count
                FROM attendance
                GROUP BY status
                ORDER BY count DESC
            """)
            
            status_distribution = {}
            for row in cur.fetchall():
                status_distribution[row[0]] = int(row[1])
            
            # Get attendance by subject
            cur.execute("""
                SELECT s.code, s.name, 
                       COUNT(CASE WHEN a.status = 'Present' THEN 1 END) as present,
                       COUNT(*) as total,
                       ROUND(100.0 * COUNT(CASE WHEN a.status = 'Present' THEN 1 END) / 
                             COUNT(*), 2) as percentage
                FROM attendance a
                JOIN subjects s ON a.subject_id = s.id
                GROUP BY s.id, s.code, s.name
                ORDER BY percentage DESC
            """)
            
            attendance_by_subject = []
            for row in cur.fetchall():
                attendance_by_subject.append({
                    'subject_code': row[0],
                    'subject_name': row[1],
                    'present': int(row[2]),
                    'total': int(row[3]),
                    'percentage': float(row[4])
                })
            
            # Get students with low attendance (< 75%)
            cur.execute("""
                SELECT s.id, s.name, s.email,
                       ROUND(100.0 * COUNT(CASE WHEN a.status = 'Present' THEN 1 END) / 
                             COUNT(*), 2) as attendance_percentage
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id
                GROUP BY s.id, s.name, s.email
                HAVING COUNT(*) > 0 AND 
                       100.0 * COUNT(CASE WHEN a.status = 'Present' THEN 1 END) / COUNT(*) < 75
                ORDER BY attendance_percentage ASC
                LIMIT 15
            """)
            
            low_attendance_students = []
            for row in cur.fetchall():
                low_attendance_students.append({
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'attendance_percentage': float(row[3])
                })
            
            return {
                'status_distribution': status_distribution,
                'attendance_by_subject': attendance_by_subject,
                'low_attendance_students': low_attendance_students,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching attendance analytics: {str(e)}")
            return {'error': str(e)}
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_department_analytics() -> Dict[str, Any]:
        """
        Get department-wise statistics and comparisons
        
        Returns:
            dict: Department metrics and analysis
        """
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Get students per department
            cur.execute("""
                SELECT d.name, COUNT(s.id) as student_count,
                       ROUND(AVG(CAST(s.cgpa AS FLOAT)), 2) as avg_cgpa
                FROM departments d
                LEFT JOIN students s ON d.id = s.department_id
                GROUP BY d.id, d.name
                ORDER BY student_count DESC
            """)
            
            departments = []
            for row in cur.fetchall():
                departments.append({
                    'name': row[0],
                    'student_count': int(row[1]),
                    'avg_cgpa': float(row[2]) if row[2] else 0.0
                })
            
            # Get top performing department
            if departments:
                top_dept = max(departments, key=lambda x: x['avg_cgpa'])
                top_dept_name = top_dept['name']
            else:
                top_dept_name = None
            
            # Get subject performance by department
            cur.execute("""
                SELECT d.name, s.code, s.name, 
                       ROUND(AVG(CAST(m.marks AS FLOAT)), 2) as avg_marks,
                       COUNT(m.id) as record_count
                FROM subjects s
                LEFT JOIN marks m ON s.id = m.subject_id
                LEFT JOIN students st ON m.student_id = st.id
                LEFT JOIN departments d ON st.department_id = d.id
                WHERE d.name IS NOT NULL
                GROUP BY d.id, d.name, s.id, s.code, s.name
                ORDER BY d.name, avg_marks DESC
            """)
            
            subject_performance = []
            for row in cur.fetchall():
                subject_performance.append({
                    'department': row[0],
                    'subject_code': row[1],
                    'subject_name': row[2],
                    'avg_marks': float(row[3]) if row[3] else 0.0,
                    'record_count': int(row[4])
                })
            
            return {
                'departments': departments,
                'top_department': top_dept_name,
                'subject_performance': subject_performance,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching department analytics: {str(e)}")
            return {'error': str(e)}
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_marks_trends(days: int = 30) -> Dict[str, Any]:
        """
        Get marks trends over time
        
        Args:
            days: Number of days to analyze (default 30)
            
        Returns:
            dict: Marks trends and distribution
        """
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Get marks distribution
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN marks >= 90 THEN '90-100'
                        WHEN marks >= 80 THEN '80-89'
                        WHEN marks >= 70 THEN '70-79'
                        WHEN marks >= 60 THEN '60-69'
                        WHEN marks >= 50 THEN '50-59'
                        ELSE 'Below 50'
                    END as range,
                    COUNT(*) as count
                FROM marks
                GROUP BY range
                ORDER BY marks DESC
            """)
            
            marks_distribution = {}
            for row in cur.fetchall():
                marks_distribution[row[0]] = int(row[1])
            
            # Get average marks by subject
            cur.execute("""
                SELECT s.code, s.name, 
                       ROUND(AVG(CAST(m.marks AS FLOAT)), 2) as avg_marks,
                       COUNT(m.id) as count
                FROM subjects s
                LEFT JOIN marks m ON s.id = m.subject_id
                GROUP BY s.id, s.code, s.name
                ORDER BY avg_marks DESC
            """)
            
            marks_by_subject = []
            for row in cur.fetchall():
                marks_by_subject.append({
                    'subject_code': row[0],
                    'subject_name': row[1],
                    'average_marks': float(row[2]) if row[2] else 0.0,
                    'record_count': int(row[3])
                })
            
            # Get passing rate (assuming 40 is passing)
            cur.execute("""
                SELECT 
                    COUNT(CASE WHEN marks >= 40 THEN 1 END) as pass_count,
                    COUNT(*) as total_count,
                    ROUND(100.0 * COUNT(CASE WHEN marks >= 40 THEN 1 END) / COUNT(*), 2) as pass_percentage
                FROM marks
            """)
            
            pass_data = cur.fetchone()
            passing_rate = {
                'pass_count': int(pass_data[0]) if pass_data else 0,
                'total_count': int(pass_data[1]) if pass_data else 0,
                'pass_percentage': float(pass_data[2]) if pass_data and pass_data[2] else 0.0
            }
            
            return {
                'marks_distribution': marks_distribution,
                'marks_by_subject': marks_by_subject,
                'passing_rate': passing_rate,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching marks trends: {str(e)}")
            return {'error': str(e)}
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_dashboard_summary() -> Dict[str, Any]:
        """
        Get comprehensive dashboard summary with all key metrics
        
        Returns:
            dict: Complete analytics summary
        """
        try:
            return {
                'overall': AnalyticsService.get_overall_statistics(),
                'performance': AnalyticsService.get_student_performance_metrics(),
                'attendance': AnalyticsService.get_attendance_analytics(),
                'departments': AnalyticsService.get_department_analytics(),
                'marks_trends': AnalyticsService.get_marks_trends(),
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating dashboard summary: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def get_student_detailed_metrics(student_id: int) -> Dict[str, Any]:
        """
        Get detailed metrics for a specific student
        
        Args:
            student_id: Student ID
            
        Returns:
            dict: Student's detailed performance metrics
        """
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Get student info
            cur.execute("""
                SELECT id, name, email, cgpa, department_id
                FROM students WHERE id = %s
            """, (student_id,))
            
            student_data = cur.fetchone()
            if not student_data:
                return {'error': 'Student not found'}
            
            student_info = {
                'id': student_data[0],
                'name': student_data[1],
                'email': student_data[2],
                'cgpa': float(student_data[3]) if student_data[3] else 0.0,
                'department_id': student_data[4]
            }
            
            # Get student's marks by subject
            cur.execute("""
                SELECT s.code, s.name, AVG(CAST(m.marks AS FLOAT)) as avg_marks,
                       COUNT(m.id) as attempts
                FROM marks m
                JOIN subjects s ON m.subject_id = s.id
                WHERE m.student_id = %s
                GROUP BY s.id, s.code, s.name
                ORDER BY avg_marks DESC
            """, (student_id,))
            
            marks_by_subject = []
            for row in cur.fetchall():
                marks_by_subject.append({
                    'subject_code': row[0],
                    'subject_name': row[1],
                    'average_marks': float(row[2]) if row[2] else 0.0,
                    'attempts': int(row[3])
                })
            
            # Get student's attendance
            cur.execute("""
                SELECT COUNT(CASE WHEN status = 'Present' THEN 1 END) as present,
                       COUNT(*) as total,
                       ROUND(100.0 * COUNT(CASE WHEN status = 'Present' THEN 1 END) / COUNT(*), 2) as percentage
                FROM attendance
                WHERE student_id = %s
            """, (student_id,))
            
            attendance_data = cur.fetchone()
            attendance = {
                'present': int(attendance_data[0]) if attendance_data else 0,
                'total': int(attendance_data[1]) if attendance_data else 0,
                'percentage': float(attendance_data[2]) if attendance_data and attendance_data[2] else 0.0
            }
            
            return {
                'student': student_info,
                'marks_by_subject': marks_by_subject,
                'attendance': attendance,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching student metrics: {str(e)}")
            return {'error': str(e)}
        finally:
            cur.close()
            conn.close()
