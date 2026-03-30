"""
Export Routes - Handle data export to PDF and Excel
"""
from flask import Blueprint, request, jsonify, send_file
from database import get_db_connection
from services.export_service import ExportService
from auth.auth_middleware import token_required, role_required
from datetime import datetime

export_bp = Blueprint('export', __name__, url_prefix='/api/export')


@export_bp.route('/student-report/<int:student_id>', methods=['GET'])
@token_required
def export_student_pdf(current_user, student_id):
    """Export individual student report as PDF"""
    format_type = request.args.get('format', 'pdf').lower()
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Fetch student info
        cur.execute('''
            SELECT id, name, email, roll_number, cgpa,
                   (SELECT department_name FROM departments WHERE id = students.department_id) as department
            FROM students WHERE id = %s
        ''', (student_id,))
        student = cur.fetchone()
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Prepare student data
        student_data = {
            'id': student[0],
            'name': student[1],
            'email': student[2],
            'roll_number': student[3],
            'cgpa': student[4],
            'department': student[5]
        }
        
        # Fetch marks
        cur.execute('''
            SELECT s.name, m.marks, m.percentage, m.grade
            FROM marks m
            JOIN subjects s ON m.subject_id = s.id
            WHERE m.student_id = %s
            ORDER BY m.created_at DESC
        ''', (student_id,))
        marks = [{'subject': m[0], 'marks': m[1], 'percentage': m[2], 'grade': m[3]} 
                 for m in cur.fetchall()]
        student_data['marks'] = marks
        
        # Fetch attendance
        cur.execute('''
            SELECT 
                COUNT(*) as total_classes,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as attended,
                ROUND(100.0 * SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) / COUNT(*), 2) as percentage
            FROM attendance WHERE student_id = %s
        ''', (student_id,))
        attendance_result = cur.fetchone()
        if attendance_result and attendance_result[0]:
            student_data['attendance'] = {
                'total_classes': attendance_result[0],
                'attended': attendance_result[1],
                'percentage': attendance_result[2],
                'status': 'Regular' if attendance_result[2] >= 75 else 'At Risk'
            }
        
        # Fetch readiness score
        cur.execute('''
            SELECT score, risk_level, placement_outlook
            FROM readiness_scores WHERE student_id = %s
            ORDER BY created_at DESC LIMIT 1
        ''', (student_id,))
        readiness_result = cur.fetchone()
        if readiness_result:
            student_data['readiness'] = {
                'score': readiness_result[0],
                'risk_level': readiness_result[1],
                'placement_outlook': readiness_result[2]
            }
        
        cur.close()
        conn.close()
        
        # Generate PDF
        pdf_buffer = ExportService.export_student_report_pdf(student_data)
        
        filename = f"Student_Report_{student_data['roll_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@export_bp.route('/class-report/<int:class_id>', methods=['GET'])
@token_required
def export_class_pdf(current_user, class_id):
    """Export class performance report as PDF"""
    # Check authorization
    if current_user.get('role') not in ['Admin', 'Faculty']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Fetch class info
        cur.execute('SELECT name FROM subjects WHERE id = %s', (class_id,))
        class_result = cur.fetchone()
        
        if not class_result:
            return jsonify({'error': 'Class not found'}), 404
        
        class_name = class_result[0]
        
        # Fetch students in class
        cur.execute('''
            SELECT s.id, s.name, s.roll_number, s.cgpa,
                   COALESCE(AVG(m.percentage), 0) as avg_marks,
                   COALESCE(
                       ROUND(100.0 * SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / 
                       NULLIF(COUNT(DISTINCT a.id), 0), 2), 0
                   ) as attendance,
                   CASE 
                       WHEN COALESCE(AVG(m.percentage), 0) < 50 THEN 'Critical'
                       WHEN COALESCE(AVG(m.percentage), 0) < 60 THEN 'At Risk'
                       ELSE 'Normal'
                   END as status
            FROM students s
            LEFT JOIN marks m ON s.id = m.student_id AND m.subject_id = %s
            LEFT JOIN attendance a ON s.id = a.student_id
            GROUP BY s.id, s.name, s.roll_number, s.cgpa
            ORDER BY avg_marks DESC
        ''', (class_id, class_id))
        
        students = [
            {
                'id': row[0],
                'name': row[1],
                'roll_number': row[2],
                'cgpa': row[3],
                'avg_marks': row[4],
                'attendance': row[5],
                'status': row[6]
            }
            for row in cur.fetchall()
        ]
        
        # Calculate statistics
        if students:
            avg_marks = sum(s['avg_marks'] for s in students) / len(students)
            avg_attendance = sum(s['attendance'] for s in students) / len(students)
            at_risk_count = sum(1 for s in students if s['avg_marks'] < 60)
            top_performers = sum(1 for s in students if s['avg_marks'] >= 80)
        else:
            avg_marks = avg_attendance = at_risk_count = top_performers = 0
        
        class_data = {
            'statistics': {
                'total_students': len(students),
                'avg_marks': avg_marks,
                'avg_attendance': avg_attendance,
                'at_risk_count': at_risk_count,
                'top_performers': top_performers
            },
            'students': students
        }
        
        cur.close()
        conn.close()
        
        # Generate PDF
        pdf_buffer = ExportService.export_class_report_pdf(class_data, class_name)
        
        filename = f"Class_Report_{class_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@export_bp.route('/students-excel', methods=['POST'])
@token_required
def export_students_excel(current_user):
    """
    Export students list to Excel
    
    Request body (optional):
    {
        "filters": {
            "department_id": 1,
            "status": "active"
        },
        "fields": ["name", "roll_number", "email", "department", "cgpa"]
    }
    """
    # Check authorization
    if current_user.get('role') not in ['Admin', 'Faculty']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    try:
        data = request.get_json() or {}
        filters = data.get('filters', {})
        fields = data.get('fields', ['name', 'roll_number', 'email', 'department', 'cgpa', 'attendance'])
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build query
        query = '''
            SELECT s.id, s.name, s.email, s.roll_number, s.cgpa,
                   d.department_name,
                   COALESCE(
                       ROUND(100.0 * SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / 
                       NULLIF(COUNT(DISTINCT a.id), 0), 2), 0
                   ) as attendance
            FROM students s
            LEFT JOIN departments d ON s.department_id = d.id
            LEFT JOIN attendance a ON s.id = a.student_id
        '''
        
        params = []
        where_clauses = []
        
        if filters.get('department_id'):
            where_clauses.append('s.department_id = %s')
            params.append(filters['department_id'])
        
        if filters.get('status'):
            where_clauses.append('s.status = %s')
            params.append(filters['status'])
        
        if where_clauses:
            query += ' WHERE ' + ' AND '.join(where_clauses)
        
        query += ' GROUP BY s.id, s.name, s.email, s.roll_number, s.cgpa, d.department_name'
        query += ' ORDER BY s.name'
        
        cur.execute(query, params)
        students = cur.fetchall()
        
        # Map to field names
        field_map = {
            'id': 0, 'name': 1, 'email': 2, 'roll_number': 3, 'cgpa': 4,
            'department': 5, 'attendance': 6
        }
        
        data_list = []
        for student in students:
            row = {}
            for field in fields:
                if field in field_map:
                    row[field] = student[field_map[field]]
            data_list.append(row)
        
        cur.close()
        conn.close()
        
        # Generate Excel
        excel_buffer = ExportService.export_to_excel(data_list, fields, "students_report")
        
        filename = f"Students_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@export_bp.route('/attendance-report/<int:subject_id>', methods=['GET'])
@token_required
def export_attendance_excel(current_user, subject_id):
    """Export attendance report for a subject"""
    # Check authorization
    if current_user.get('role') not in ['Faculty', 'Admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Fetch subject info
        cur.execute('SELECT name FROM subjects WHERE id = %s', (subject_id,))
        subject = cur.fetchone()
        
        if not subject:
            return jsonify({'error': 'Subject not found'}), 404
        
        # Fetch attendance data
        cur.execute('''
            SELECT s.name, s.roll_number, 
                   COUNT(*) as total_classes,
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present,
                   ROUND(100.0 * SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) 
                         / COUNT(*), 2) as percentage
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id AND a.subject_id = %s
            GROUP BY s.id, s.name, s.roll_number
            ORDER BY percentage DESC
        ''', (subject_id, subject_id))
        
        data_list = []
        for row in cur.fetchall():
            data_list.append({
                'Student Name': row[0],
                'Roll Number': row[1],
                'Total Classes': row[2] or 0,
                'Present': row[3] or 0,
                'Attendance %': row[4] or 0
            })
        
        cur.close()
        conn.close()
        
        fields = ['Student Name', 'Roll Number', 'Total Classes', 'Present', 'Attendance %']
        excel_buffer = ExportService.export_to_excel(data_list, fields, "attendance_report")
        
        filename = f"Attendance_{subject[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
