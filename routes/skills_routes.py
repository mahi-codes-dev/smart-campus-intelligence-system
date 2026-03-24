from flask import Blueprint, request, jsonify
from services.skills_service import add_skill, assign_skill, get_student_skills
from auth.auth_middleware import token_required, role_required
from database import get_db_connection

skills_bp = Blueprint("skills_bp", __name__)


# Add new skill (Admin)
@skills_bp.route("/skills", methods=["POST"])
@token_required
@role_required("Admin")
def create_skill():
    try:
        data = request.get_json()
        name = data["name"]

        add_skill(name)

        return jsonify({"message": "Skill added"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# # Assign skill to student (Admin)
# @skills_bp.route("/student-skills", methods=["POST"])
# @token_required
# @role_required("Admin")
# def assign_skill_to_student():
#     try:
#         data = request.get_json()

#         student_id = data["student_id"]
#         skill_id = data["skill_id"]

#         assign_skill(student_id, skill_id)

#         return jsonify({"message": "Skill assigned"}), 201

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# # Get student skills
# @skills_bp.route("/student-skills/<int:student_id>", methods=["GET"])
# @token_required
# def fetch_student_skills(student_id):
#     try:
#         skills = get_student_skills(student_id)
#         return jsonify(skills), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# Assign skill to student (Faculty)
@skills_bp.route("/faculty/student-skills", methods=["POST"])
@token_required
@role_required("Faculty")   # 🔥 CHANGED
def assign_skill_to_student():
    try:
        data = request.get_json()

        if not all(k in data for k in ("student_id", "skill_id")):
            return jsonify({"error": "Missing fields"}), 400

        student_id = data["student_id"]
        skill_id = data["skill_id"]

        assign_skill(student_id, skill_id)

        return jsonify({"message": "Skill assigned"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Get student skills (Student can view their own skills)
@skills_bp.route("/student/skills", methods=["GET"])
@token_required
@role_required("Student")
def get_my_skills():
    try:
        user_id = request.user["user_id"]

        conn = get_db_connection()
        cur = conn.cursor()

        # 🔥 Get student_id using user_id
        cur.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
        student = cur.fetchone()

        if not student:
            return jsonify({"error": "Student not found"}), 404

        student_id = student[0]

        # Fetch skills
        skills = get_student_skills(student_id)

        cur.close()
        conn.close()

        return jsonify(skills), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500