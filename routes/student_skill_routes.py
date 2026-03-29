from flask import Blueprint, request, jsonify
from services.student_skill_service import get_student_skills
from services.skills_service import assign_skill, get_or_create_skill
from services.student_service import get_student_record_by_user_id
from auth.auth_middleware import token_required, role_required

student_skill_bp = Blueprint("student_skill_bp", __name__)


@student_skill_bp.route("/student/skills", methods=["POST"])
@token_required
@role_required("Student")
def add_skill():
    try:
        data = request.get_json() or {}
        print("STUDENT_SKILL_ADD_REQUEST:", data)
        student = get_student_record_by_user_id(request.user["user_id"])  # type: ignore

        if not student:
            return jsonify({"error": "Student not found"}), 404

        student_id = student["id"]
        requested_student_id = data.get("student_id")

        if requested_student_id is not None and requested_student_id != student_id:
            return jsonify({"error": "Students can only add skills to their own profile"}), 403

        skill_id = data.get("skill_id")

        if skill_id is None:
            skill_name = (data.get("skill_name") or "").strip()

            if not skill_name:
                return jsonify({"error": "skill_name or skill_id is required"}), 400

            skill_id = get_or_create_skill(skill_name)

        action = assign_skill(student_id, skill_id, data.get("skill_level") or "Intermediate")

        return jsonify({
            "message": "Skill updated successfully" if action == "updated" else "Skill added successfully",
            "student_id": student_id,
            "skill_id": skill_id,
            "skill_level": data.get("skill_level") or "Intermediate",
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@student_skill_bp.route("/student/skills/<int:student_id>", methods=["GET"])
@token_required
def get_skills(student_id):
    try:
        if request.user.get("role_id") == 3:  # type: ignore
            student = get_student_record_by_user_id(request.user["user_id"])  # type: ignore
            if not student or student["id"] != student_id:
                return jsonify({"error": "Students can only view their own skills"}), 403

        skills = get_student_skills(student_id)
        return jsonify(skills), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
