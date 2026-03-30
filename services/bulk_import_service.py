"""
Bulk Import Service - Handles CSV import for Students, Marks, and Attendance
"""
import csv
import io
from datetime import datetime
from database import get_db_connection
from services.student_service import ensure_student_table_consistency, ensure_department_exists
from services.subject_service import ensure_subject_table_consistency
from services.marks_service import ensure_marks_table_consistency
from services.attendance_service import ensure_attendance_table_consistency
from services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)


class BulkImportService:
    """Service for bulk importing data via CSV"""
    
    # CSV column mappings for different import types
    STUDENT_COLUMNS = {
        'email': str,
        'name': str,
        'department': str,
        'contact': str,
        'cgpa': float,
    }
    
    MARKS_COLUMNS = {
        'student_email': str,
        'subject_code': str,
        'marks': int,
        'exam_type': str,
    }
    
    ATTENDANCE_COLUMNS = {
        'student_email': str,
        'subject_code': str,
        'date': str,
        'status': str,  # Present, Absent, Late
    }
    
    SKILLS_COLUMNS = {
        'student_email': str,
        'skill_name': str,
        'proficiency': str,  # Beginner, Intermediate, Advanced
    }
    
    @staticmethod
    def validate_csv_headers(headers, expected_columns):
        """
        Validate CSV headers match expected columns
        
        Args:
            headers: List of header names from CSV
            expected_columns: Dict of expected column names
        
        Returns:
            tuple: (is_valid, missing_columns, extra_columns)
        """
        expected_set = set(expected_columns.keys())
        actual_set = set([h.lower().strip() for h in headers])
        
        missing = expected_set - actual_set
        extra = actual_set - expected_set
        
        is_valid = len(missing) == 0
        return is_valid, list(missing), list(extra)
    
    @staticmethod
    def parse_csv(file_content):
        """
        Parse CSV file content
        
        Args:
            file_content: File content (bytes or string)
        
        Returns:
            tuple: (headers, rows, error)
        """
        try:
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            
            f = io.StringIO(file_content)
            reader = csv.reader(f)
            
            headers = next(reader, None)
            if not headers:
                return None, None, "CSV file is empty"
            
            # Clean headers
            headers = [h.lower().strip() for h in headers]
            
            rows = list(reader)
            return headers, rows, None
            
        except Exception as e:
            return None, None, f"CSV parsing error: {str(e)}"
    
    @staticmethod
    def import_students(file_content, user_id):
        """
        Import students from CSV
        
        Args:
            file_content: CSV file content
            user_id: ID of importing admin (for audit)
        
        Returns:
            dict: {success: bool, message: str, imported: int, errors: list, duplicates: int}
        """
        headers, rows, parse_error = BulkImportService.parse_csv(file_content)
        
        if parse_error:
            return {
                'success': False,
                'message': parse_error,
                'imported': 0,
                'errors': [],
                'duplicates': 0
            }
        
        # Ensure rows is not None
        if headers is None or rows is None:
            return {
                'success': False,
                'message': 'Invalid CSV format',
                'imported': 0,
                'errors': ['CSV file is empty or invalid'],
                'duplicates': 0
            }
        
        # Validate headers
        is_valid, missing, extra = BulkImportService.validate_csv_headers(
            headers, BulkImportService.STUDENT_COLUMNS
        )
        
        if not is_valid:
            return {
                'success': False,
                'message': f"Missing required columns: {', '.join(missing)}",
                'imported': 0,
                'errors': [f"Missing columns: {', '.join(missing)}"],
                'duplicates': 0
            }
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            ensure_student_table_consistency(conn)
            
            imported_count = 0
            duplicate_count = 0
            errors = []
            imported_students = []
            
            # Start transaction
            conn.set_isolation_level(3)  # SERIALIZABLE
            
            for row_num, row in enumerate(rows, start=2):
                try:
                    if len(row) < len(headers):
                        row.extend([''] * (len(headers) - len(row)))
                    
                    row_dict = {headers[i]: row[i].strip() if i < len(row) else '' 
                               for i in range(len(headers))}
                    
                    email = row_dict.get('email', '').strip()
                    name = row_dict.get('name', '').strip()
                    department = row_dict.get('department', '').strip()
                    contact = row_dict.get('contact', '').strip()
                    cgpa_str = row_dict.get('cgpa', '').strip()
                    
                    # Validation
                    if not email or not name:
                        errors.append(f"Row {row_num}: Email and name are required")
                        continue
                    
                    if not email.count('@'):
                        errors.append(f"Row {row_num}: Invalid email format")
                        continue
                    
                    if not department:
                        errors.append(f"Row {row_num}: Department is required")
                        continue
                    
                    try:
                        cgpa = float(cgpa_str) if cgpa_str else 0.0
                        if cgpa < 0 or cgpa > 10:
                            errors.append(f"Row {row_num}: CGPA must be between 0 and 10")
                            continue
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid CGPA format")
                        continue
                    
                    # Check for duplicate
                    cur.execute("SELECT id FROM students WHERE email = %s", (email,))
                    if cur.fetchone():
                        duplicate_count += 1
                        errors.append(f"Row {row_num}: Student with email {email} already exists (skipped)")
                        continue
                    
                    # Ensure department exists
                    dept_result = ensure_department_exists(department, conn)
                    dept_id = dept_result['id'] if dept_result else 1
                    
                    # Insert student
                    cur.execute(
                        """
                        INSERT INTO students (name, email, department_id, contact, cgpa)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (name, email, dept_id, contact, cgpa)
                    )
                    
                    result = cur.fetchone()
                    if not result:
                        errors.append(f"Row {row_num}: Failed to insert student")
                        continue
                    
                    student_id = result[0]
                    imported_students.append({
                        'id': student_id,
                        'email': email,
                        'name': name
                    })
                    imported_count += 1
                    
                except Exception as row_error:
                    errors.append(f"Row {row_num}: {str(row_error)}")
            
            conn.commit()
            
            # Send notification
            if imported_count > 0:
                subject = "✅ Bulk Student Import Completed"
                message = f"Successfully imported {imported_count} students."
                if duplicate_count > 0:
                    message += f" {duplicate_count} duplicates were skipped."
                if errors:
                    message += f" {len(errors)} rows had errors."
                
                logger.info(f"Bulk import completed: {imported_count} students imported")
            
            return {
                'success': True,
                'message': f"Successfully imported {imported_count} student(s)",
                'imported': imported_count,
                'errors': errors,
                'duplicates': duplicate_count,
                'data': imported_students
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Bulk import error: {str(e)}")
            return {
                'success': False,
                'message': f"Import failed: {str(e)}",
                'imported': 0,
                'errors': [str(e)],
                'duplicates': 0
            }
        
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def import_marks(file_content, user_id):
        """
        Import marks from CSV
        
        Args:
            file_content: CSV file content
            user_id: ID of importing admin
        
        Returns:
            dict: Import result with statistics
        """
        headers, rows, parse_error = BulkImportService.parse_csv(file_content)
        
        if parse_error:
            return {
                'success': False,
                'message': parse_error,
                'imported': 0,
                'errors': [],
                'duplicates': 0
            }
        
        # Ensure rows is not None
        if headers is None or rows is None:
            return {
                'success': False,
                'message': 'Invalid CSV format',
                'imported': 0,
                'errors': ['CSV file is empty or invalid'],
                'duplicates': 0
            }
        
        # Validate headers
        is_valid, missing, extra = BulkImportService.validate_csv_headers(
            headers, BulkImportService.MARKS_COLUMNS
        )
        
        if not is_valid:
            return {
                'success': False,
                'message': f"Missing required columns: {', '.join(missing)}",
                'imported': 0,
                'errors': [f"Missing columns: {', '.join(missing)}"],
                'duplicates': 0
            }
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            ensure_marks_table_consistency(conn)
            
            imported_count = 0
            errors = []
            
            conn.set_isolation_level(3)  # SERIALIZABLE
            
            for row_num, row in enumerate(rows, start=2):
                try:
                    if len(row) < len(headers):
                        row.extend([''] * (len(headers) - len(row)))
                    
                    row_dict = {headers[i]: row[i].strip() if i < len(row) else '' 
                               for i in range(len(headers))}
                    
                    student_email = row_dict.get('student_email', '').strip()
                    subject_code = row_dict.get('subject_code', '').strip()
                    marks_str = row_dict.get('marks', '').strip()
                    exam_type = row_dict.get('exam_type', 'Mid-Sem').strip()
                    
                    # Validation
                    if not student_email or not subject_code or not marks_str:
                        errors.append(f"Row {row_num}: Email, subject code, and marks are required")
                        continue
                    
                    try:
                        marks = int(marks_str)
                        if marks < 0 or marks > 100:
                            errors.append(f"Row {row_num}: Marks must be between 0 and 100")
                            continue
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid marks format")
                        continue
                    
                    # Get student ID
                    cur.execute("SELECT id FROM students WHERE email = %s", (student_email,))
                    student_result = cur.fetchone()
                    if not student_result:
                        errors.append(f"Row {row_num}: Student with email {student_email} not found")
                        continue
                    
                    student_id = student_result[0]
                    
                    # Get subject ID
                    cur.execute("SELECT id FROM subjects WHERE code = %s", (subject_code,))
                    subject_result = cur.fetchone()
                    if not subject_result:
                        errors.append(f"Row {row_num}: Subject with code {subject_code} not found")
                        continue
                    
                    subject_id = subject_result[0]
                    
                    # Insert marks
                    cur.execute(
                        """
                        INSERT INTO marks (student_id, subject_id, marks, exam_type)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (student_id, subject_id, marks, exam_type)
                    )
                    
                    imported_count += 1
                    
                except Exception as row_error:
                    errors.append(f"Row {row_num}: {str(row_error)}")
            
            conn.commit()
            
            return {
                'success': True,
                'message': f"Successfully imported {imported_count} mark(s)",
                'imported': imported_count,
                'errors': errors,
                'duplicates': 0
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Marks import error: {str(e)}")
            return {
                'success': False,
                'message': f"Import failed: {str(e)}",
                'imported': 0,
                'errors': [str(e)],
                'duplicates': 0
            }
        
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def import_attendance(file_content, user_id):
        """
        Import attendance records from CSV
        
        Args:
            file_content: CSV file content
            user_id: ID of importing admin
        
        Returns:
            dict: Import result with statistics
        """
        headers, rows, parse_error = BulkImportService.parse_csv(file_content)
        
        if parse_error:
            return {
                'success': False,
                'message': parse_error,
                'imported': 0,
                'errors': [],
                'duplicates': 0
            }
        
        # Ensure rows is not None
        if headers is None or rows is None:
            return {
                'success': False,
                'message': 'Invalid CSV format',
                'imported': 0,
                'errors': ['CSV file is empty or invalid'],
                'duplicates': 0
            }
        
        # Validate headers
        is_valid, missing, extra = BulkImportService.validate_csv_headers(
            headers, BulkImportService.ATTENDANCE_COLUMNS
        )
        
        if not is_valid:
            return {
                'success': False,
                'message': f"Missing required columns: {', '.join(missing)}",
                'imported': 0,
                'errors': [f"Missing columns: {', '.join(missing)}"],
                'duplicates': 0
            }
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            ensure_attendance_table_consistency(conn)
            
            imported_count = 0
            errors = []
            
            conn.set_isolation_level(3)  # SERIALIZABLE
            
            valid_statuses = ['present', 'absent', 'late', 'excused']
            
            for row_num, row in enumerate(rows, start=2):
                try:
                    if len(row) < len(headers):
                        row.extend([''] * (len(headers) - len(row)))
                    
                    row_dict = {headers[i]: row[i].strip() if i < len(row) else '' 
                               for i in range(len(headers))}
                    
                    student_email = row_dict.get('student_email', '').strip()
                    subject_code = row_dict.get('subject_code', '').strip()
                    date_str = row_dict.get('date', '').strip()
                    status = row_dict.get('status', 'Present').strip().lower()
                    
                    # Validation
                    if not student_email or not subject_code or not date_str:
                        errors.append(f"Row {row_num}: Email, subject code, and date are required")
                        continue
                    
                    if status not in valid_statuses:
                        errors.append(f"Row {row_num}: Status must be one of {', '.join(valid_statuses)}")
                        continue
                    
                    # Validate date format
                    try:
                        from datetime import datetime
                        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid date format (use YYYY-MM-DD)")
                        continue
                    
                    # Get student ID
                    cur.execute("SELECT id FROM students WHERE email = %s", (student_email,))
                    student_result = cur.fetchone()
                    if not student_result:
                        errors.append(f"Row {row_num}: Student with email {student_email} not found")
                        continue
                    
                    student_id = student_result[0]
                    
                    # Get subject ID
                    cur.execute("SELECT id FROM subjects WHERE code = %s", (subject_code,))
                    subject_result = cur.fetchone()
                    if not subject_result:
                        errors.append(f"Row {row_num}: Subject with code {subject_code} not found")
                        continue
                    
                    subject_id = subject_result[0]
                    
                    # Insert attendance
                    cur.execute(
                        """
                        INSERT INTO attendance (student_id, subject_id, date, status)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (student_id, subject_id, attendance_date, status.capitalize())
                    )
                    
                    imported_count += 1
                    
                except Exception as row_error:
                    errors.append(f"Row {row_num}: {str(row_error)}")
            
            conn.commit()
            
            return {
                'success': True,
                'message': f"Successfully imported {imported_count} attendance record(s)",
                'imported': imported_count,
                'errors': errors,
                'duplicates': 0
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Attendance import error: {str(e)}")
            return {
                'success': False,
                'message': f"Import failed: {str(e)}",
                'imported': 0,
                'errors': [str(e)],
                'duplicates': 0
            }
        
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_import_templates():
        """
        Get example CSV templates for all import types
        
        Returns:
            dict: Templates with headers and example rows
        """
        return {
            'students': {
                'headers': list(BulkImportService.STUDENT_COLUMNS.keys()),
                'example': [
                    ['student1@campus.edu', 'John Doe', 'Computer Science', '9876543210', '8.5'],
                    ['student2@campus.edu', 'Jane Smith', 'Electronics', '9876543211', '9.2'],
                ]
            },
            'marks': {
                'headers': list(BulkImportService.MARKS_COLUMNS.keys()),
                'example': [
                    ['student1@campus.edu', 'CS101', '85', 'Mid-Sem'],
                    ['student1@campus.edu', 'CS102', '92', 'End-Sem'],
                ]
            },
            'attendance': {
                'headers': list(BulkImportService.ATTENDANCE_COLUMNS.keys()),
                'example': [
                    ['student1@campus.edu', 'CS101', '2026-01-15', 'Present'],
                    ['student1@campus.edu', 'CS101', '2026-01-16', 'Absent'],
                ]
            },
            'skills': {
                'headers': list(BulkImportService.SKILLS_COLUMNS.keys()),
                'example': [
                    ['student1@campus.edu', 'Python', 'Advanced'],
                    ['student1@campus.edu', 'JavaScript', 'Intermediate'],
                ]
            }
        }
    
    @staticmethod
    def get_import_statistics(filters=None):
        """
        Get import history and statistics
        
        Args:
            filters: Optional dict with date range, import type, etc.
        
        Returns:
            dict: Statistics including total imports, success rate, etc.
        """
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Get student count
            cur.execute("SELECT COUNT(*) FROM students")
            result = cur.fetchone()
            student_count = result[0] if result else 0
            
            # Get mark records count
            cur.execute("SELECT COUNT(*) FROM marks")
            result = cur.fetchone()
            mark_records = result[0] if result else 0
            
            # Get attendance records count
            cur.execute("SELECT COUNT(*) FROM attendance")
            result = cur.fetchone()
            attendance_records = result[0] if result else 0
            
            return {
                'total_students': student_count,
                'total_mark_records': mark_records,
                'total_attendance_records': attendance_records,
                'system_ready': True
            }
            
        except Exception as e:
            logger.error(f"Statistics fetch error: {str(e)}")
            return {
                'total_students': 0,
                'total_mark_records': 0,
                'total_attendance_records': 0,
                'system_ready': False,
                'error': str(e)
            }
        
        finally:
            cur.close()
            conn.close()
