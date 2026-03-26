from flask import Blueprint, request, jsonify
from services.student_skill_service import add_student_skill, get_student_skills
from auth.auth_middleware import token_required, role_required

student_skill_bp = Blueprint("student_skill_bp", __name__)


# ✅ Add Skill
@student_skill_bp.route("/student/skills", methods=["POST"])
@token_required
@role_required("Student")
def add_skill():
    try:
        data = request.get_json()

        student_id = data["student_id"]
        skill_id = data["skill_id"]

        add_student_skill(student_id, skill_id)

        return jsonify({"message": "Skill added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Get Skills
@student_skill_bp.route("/student/skills/<int:student_id>", methods=["GET"])
@token_required
def get_skills(student_id):
    try:
        skills = get_student_skills(student_id)
        return jsonify(skills), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500