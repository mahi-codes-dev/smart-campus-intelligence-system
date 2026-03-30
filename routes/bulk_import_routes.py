"""
Bulk Import Routes - API endpoints for CSV bulk import operations
"""
from flask import Blueprint, jsonify, request
from auth.auth_middleware import token_required, role_required
from services.bulk_import_service import BulkImportService
import logging

bulk_import_bp = Blueprint("bulk_import_bp", __name__)
logger = logging.getLogger(__name__)


@bulk_import_bp.route("/admin/bulk-import/students", methods=["POST"])
@token_required
@role_required("Admin")
def bulk_import_students():
    """
    Bulk import students from CSV file
    Expected format: email, name, department, contact, cgpa
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if not file or not file.filename or file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "Only CSV files are supported"}), 400
        
        # Read file content
        file_content = file.read()
        
        # Get user ID from token (request.user set by @token_required)
        user_id = getattr(request, 'user_id', None)  # type: ignore
        
        # Import students
        result = BulkImportService.import_students(file_content, user_id)
        
        status_code = 201 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Bulk import students error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bulk_import_bp.route("/admin/bulk-import/marks", methods=["POST"])
@token_required
@role_required("Admin")
def bulk_import_marks():
    """
    Bulk import marks from CSV file
    Expected format: student_email, subject_code, marks, exam_type
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if not file or not file.filename or file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "Only CSV files are supported"}), 400
        
        # Read file content
        file_content = file.read()
        
        # Get user ID from token
        user_id = getattr(request, 'user_id', None)  # type: ignore
        
        # Import marks
        result = BulkImportService.import_marks(file_content, user_id)
        
        status_code = 201 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Bulk import marks error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bulk_import_bp.route("/admin/bulk-import/attendance", methods=["POST"])
@token_required
@role_required("Admin")
def bulk_import_attendance():
    """
    Bulk import attendance records from CSV file
    Expected format: student_email, subject_code, date (YYYY-MM-DD), status
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if not file or not file.filename or file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "Only CSV files are supported"}), 400
        
        # Read file content
        file_content = file.read()
        
        # Get user ID from token
        user_id = getattr(request, 'user_id', None)  # type: ignore
        
        # Import attendance
        result = BulkImportService.import_attendance(file_content, user_id)
        
        status_code = 201 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Bulk import attendance error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bulk_import_bp.route("/admin/bulk-import/templates", methods=["GET"])
@token_required
@role_required("Admin")
def get_csv_templates():
    """
    Get example CSV templates for all import types
    """
    try:
        templates = BulkImportService.get_import_templates()
        return jsonify(templates), 200
        
    except Exception as e:
        logger.error(f"Get templates error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bulk_import_bp.route("/admin/bulk-import/statistics", methods=["GET"])
@token_required
@role_required("Admin")
def get_bulk_import_statistics():
    """
    Get import statistics and system readiness
    """
    try:
        stats = BulkImportService.get_import_statistics()
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Get statistics error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bulk_import_bp.route("/admin/bulk-import/validate-csv", methods=["POST"])
@token_required
@role_required("Admin")
def validate_csv():
    """
    Validate CSV file format and headers
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        import_type = request.form.get('import_type', 'students')
        
        if not file or not file.filename or file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "Only CSV files are supported"}), 400
        
        # Read and parse file
        file_content = file.read()
        headers, rows, parse_error = BulkImportService.parse_csv(file_content)
        
        if parse_error:
            return jsonify({
                "valid": False,
                "error": parse_error,
                "headers": None,
                "row_count": 0
            }), 400
        
        # Ensure rows is not None for length check
        if rows is None:
            rows = []  # type: ignore
        
        # Get expected columns based on import type
        if import_type == 'students':
            expected_columns = BulkImportService.STUDENT_COLUMNS
        elif import_type == 'marks':
            expected_columns = BulkImportService.MARKS_COLUMNS
        elif import_type == 'attendance':
            expected_columns = BulkImportService.ATTENDANCE_COLUMNS
        elif import_type == 'skills':
            expected_columns = BulkImportService.SKILLS_COLUMNS
        else:
            return jsonify({
                "valid": False,
                "error": f"Unknown import type: {import_type}"
            }), 400
        
        # Validate headers
        is_valid, missing, extra = BulkImportService.validate_csv_headers(headers, expected_columns)
        
        return jsonify({
            "valid": is_valid,
            "headers": headers,
            "row_count": len(rows),
            "expected_columns": list(expected_columns.keys()),
            "missing_columns": missing,
            "extra_columns": extra,
            "import_type": import_type
        }), 200 if is_valid else 400
        
    except Exception as e:
        logger.error(f"CSV validation error: {str(e)}")
        return jsonify({"error": str(e)}), 500
