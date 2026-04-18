import logging

from flask import Blueprint, jsonify

from auth.auth_middleware import role_required, token_required
from database import get_db_connection
from services.readiness_service import calculate_readiness

logger = logging.getLogger(__name__)

faculty_bp = Blueprint("faculty_bp", __name__)


@faculty_bp.route("/faculty/students", methods=["GET"])
@token_required
@role_required("Faculty")
def get_all_students_performance():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, email FROM students")
                students = cur.fetchall()

        result = []

        for student in students:
            student_id = student[0]
            data = calculate_readiness(student_id)

            result.append({
                "id": student_id,
                "name": student[1],
                "email": student[2],
                "readiness_score": data["final_score"],
                "status": data["status"],
            })

        return jsonify(result), 200

    except Exception as e:
        logger.exception("get_all_students_performance failed")
        return jsonify({"error": "An internal error occurred"}), 500


@faculty_bp.route("/faculty/marks", methods=["POST"])
@token_required
@role_required("Faculty")
def add_marks():
    try:
        from flask import request

        data = request.get_json()

        student_id = data["student_id"]
        subject_id = data["subject_id"]
        marks = data["marks"]

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO marks (student_id, subject_id, marks)
                    VALUES (%s, %s, %s)
                    """,
                    (student_id, subject_id, marks),
                )

        return jsonify({"message": "Marks added successfully"}), 201

    except Exception as e:
        logger.exception("add_marks failed")
        return jsonify({"error": "An internal error occurred"}), 500
