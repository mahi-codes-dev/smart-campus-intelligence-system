from flask import Blueprint, request, jsonify
from services.skills_service import add_skill, assign_skill, get_student_skills
from auth.auth_middleware import token_required, role_required

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


# Assign skill to student (Admin)
@skills_bp.route("/student-skills", methods=["POST"])
@token_required
@role_required("Admin")
def assign_skill_to_student():
    try:
        data = request.get_json()

        student_id = data["student_id"]
        skill_id = data["skill_id"]

        assign_skill(student_id, skill_id)

        return jsonify({"message": "Skill assigned"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Get student skills
@skills_bp.route("/student-skills/<int:student_id>", methods=["GET"])
@token_required
def fetch_student_skills(student_id):
    try:
        skills = get_student_skills(student_id)
        return jsonify(skills), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500