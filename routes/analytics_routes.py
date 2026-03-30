"""
Analytics Routes - API endpoints for analytics and dashboard data
Provides endpoints for charts, metrics, and performance insights
"""
from flask import Blueprint, jsonify, request
from auth.auth_middleware import token_required, role_required
from services.analytics_service import AnalyticsService
import logging

analytics_bp = Blueprint("analytics_bp", __name__)
logger = logging.getLogger(__name__)


@analytics_bp.route("/api/analytics/dashboard-summary", methods=["GET"])
@token_required
def get_dashboard_summary():
    """
    Get comprehensive dashboard summary with all metrics
    
    Returns:
        JSON with overall, performance, attendance, and departmental analytics
    """
    try:
        summary = AnalyticsService.get_dashboard_summary()
        return jsonify(summary), 200
    except Exception as e:
        logger.error(f"Dashboard summary error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/analytics/overall-statistics", methods=["GET"])
@token_required
def get_overall_statistics():
    """
    Get system-wide statistics
    
    Returns:
        JSON with overall counts, averages, and summaries
    """
    try:
        stats = AnalyticsService.get_overall_statistics()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Overall statistics error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/analytics/performance", methods=["GET"])
@token_required
def get_performance_metrics():
    """
    Get student performance metrics and distributions
    
    Returns:
        JSON with CGPA distribution, top performers, and at-risk students
    """
    try:
        metrics = AnalyticsService.get_student_performance_metrics()
        return jsonify(metrics), 200
    except Exception as e:
        logger.error(f"Performance metrics error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/analytics/attendance", methods=["GET"])
@token_required
def get_attendance_analytics():
    """
    Get attendance patterns and analytics
    
    Returns:
        JSON with attendance distribution and trends
    """
    try:
        analytics = AnalyticsService.get_attendance_analytics()
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Attendance analytics error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/analytics/departments", methods=["GET"])
@token_required
def get_department_analytics():
    """
    Get department-wise statistics and analysis
    
    Returns:
        JSON with departmental metrics and comparisons
    """
    try:
        analytics = AnalyticsService.get_department_analytics()
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Department analytics error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/analytics/marks-trends", methods=["GET"])
@token_required
def get_marks_trends():
    """
    Get marks trends and distribution
    
    Query parameters:
        days: Number of days to analyze (default 30)
    
    Returns:
        JSON with marks distribution and trends
    """
    try:
        days = request.args.get('days', 30, type=int)
        if days < 1 or days > 365:
            days = 30
        
        trends = AnalyticsService.get_marks_trends(days)
        return jsonify(trends), 200
    except Exception as e:
        logger.error(f"Marks trends error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/analytics/student/<int:student_id>", methods=["GET"])
@token_required
def get_student_metrics(student_id):
    """
    Get detailed metrics for a specific student
    
    Args:
        student_id: Student ID
    
    Returns:
        JSON with student's detailed performance metrics
    """
    try:
        metrics = AnalyticsService.get_student_detailed_metrics(student_id)
        
        if 'error' in metrics:
            return jsonify(metrics), 404
        
        return jsonify(metrics), 200
    except Exception as e:
        logger.error(f"Student metrics error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/analytics/export-pdf", methods=["GET"])
@token_required
@role_required("Admin")
def export_analytics_pdf():
    """
    Export analytics report as PDF (admin only)
    
    Returns:
        PDF file with complete analytics report
    """
    try:
        # PDF export feature - coming in Phase 7
        return jsonify({"message": "PDF export feature coming soon"}), 200
        
    except Exception as e:
        logger.error(f"PDF export error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/analytics/export-excel", methods=["GET"])
@token_required
@role_required("Admin")
def export_analytics_excel():
    """
    Export analytics report as Excel (admin only)
    
    Returns:
        Excel file with complete analytics data
    """
    try:
        # Excel export feature - coming in Phase 7
        return jsonify({"message": "Excel export feature coming soon"}), 200
        
    except Exception as e:
        logger.error(f"Excel export error: {str(e)}")
        return jsonify({"error": str(e)}), 500
