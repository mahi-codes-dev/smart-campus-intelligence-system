from flask import Blueprint, jsonify
from database import get_db_connection
from auth.auth_middleware import token_required, role_required
from services.readiness_service import calculate_readiness

faculty_bp = Blueprint("faculty_bp", __name__)


# ✅ GET ALL STUDENTS WITH PERFORMANCE
@faculty_bp.route("/faculty/students", methods=["GET"])
@token_required
@role_required("Faculty")
def get_all_students_performance():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 🔥 Get all students
        cur.execute("SELECT id, name, email FROM students")
        students = cur.fetchall()

        result = []

        for student in students:
            student_id = student[0]

            # 🔥 Calculate readiness
            data = calculate_readiness(student_id)

            result.append({
                "id": student_id,
                "name": student[1],
                "email": student[2],
                "readiness_score": data["final_score"],
                "status": data["status"]
            })

        cur.close()
        conn.close()

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
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

        conn = get_db_connection()
        cur = conn.cursor()

        # 🔥 Insert marks
        cur.execute("""
            INSERT INTO marks (student_id, subject_id, marks)
            VALUES (%s, %s, %s)
        """, (student_id, subject_id, marks))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Marks added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500