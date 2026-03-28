from flask import Flask, jsonify, request
import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv
from database import get_db_connection
from routes.student_routes import student_bp
from auth.auth_routes import auth_bp
from routes.subject_routes import subject_bp
from routes.attendance_routes import attendance_bp
from routes.marks_routes import marks_bp
from routes.readiness_routes import readiness_bp
from routes.skills_routes import skills_bp
from routes.mock_routes import mock_bp
from routes.faculty_routes import faculty_bp
from routes.student_dashboard_routes import student_dashboard_bp
from routes.faculty_dashboard_routes import faculty_dashboard_bp
from routes.student_skill_routes import student_skill_bp
from routes.admin_dashboard_routes import admin_dashboard_bp
from routes.prediction_routes import prediction_bp
from services.student_service import ensure_student_table_consistency
# from routes.readiness_routes import get_top_students
from flask import render_template, render_template_string


# Load environment variables
load_dotenv()

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent

try:
    ensure_student_table_consistency()
except Exception as schema_error:
    print("STUDENT_SCHEMA_SYNC_ERROR:", schema_error)

app.register_blueprint(student_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(subject_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(marks_bp)
app.register_blueprint(readiness_bp)
app.register_blueprint(skills_bp)
app.register_blueprint(mock_bp)
app.register_blueprint(faculty_bp)
app.register_blueprint(student_dashboard_bp)
app.register_blueprint(faculty_dashboard_bp)
app.register_blueprint(student_skill_bp)
app.register_blueprint(admin_dashboard_bp)
app.register_blueprint(prediction_bp)
# app.register_blueprint(get_top_students)  # 🔥 NEW BLUEPRINT FOR TOP STUDENTS

@app.route("/")
def home():
    return render_template("login.html")
    # try:
    #     conn = get_db_connection()
    #     conn.close()
    #     return jsonify({"message": "Secure Database Connected Successfully 🔐"}), 200
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500

@app.route("/health")
def health_check():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({
            "status": "healthy",
            "database": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }), 500
    

@app.route("/create-table")
def create_table():
    try:
        ensure_student_table_consistency()

        return "Students table created successfully 🎯"

    except Exception as e:
        return f"Error: {e}"
    

@app.route("/add-student", methods=["POST"])
def add_student():
    try:
        data = request.get_json()

        if not data or "name" not in data or "email" not in data or "department" not in data:
            return jsonify({"error": "Missing required fields"}), 400

        name = data["name"]
        email = data["email"]
        department = data["department"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO students (name, email, department)
            VALUES (%s, %s, %s);
        """, (name, email, department))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Student added successfully 🎓"}), 201

    except psycopg2.errors.UniqueViolation:
        return jsonify({"error": "Email already exists"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/update-student/<int:id>", methods=["PUT"])
def update_student(id):
    try:
        data = request.get_json()

        name = data["name"]
        email = data["email"]
        department = data["department"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE students
            SET name = %s,
                email = %s,
                department = %s
            WHERE id = %s;
        """, (name, email, department, id))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Student updated successfully 🔄"})

    except Exception as e:
        return jsonify({"error": str(e)})
    

@app.route("/delete-student/<int:id>", methods=["DELETE"])
def delete_student(id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM students
            WHERE id = %s;
        """, (id,))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Student deleted successfully 🗑️"})

    except Exception as e:
        return jsonify({"error": str(e)})
    
# @app.route("/test-mock")
# def test_mock():
#     return "Mock route test working"


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route('/student-dashboard')
def student_dashboard():
    return render_template('dashboard_student.html')

@app.route('/faculty-dashboard')
def faculty_dashboard():
    return render_template('dashboard_faculty.html')

@app.route('/student-progress')
def student_progress():
    return render_template('student_progress.html')

@app.route('/student-skills')
def student_skills():
    return render_template('student_skills.html')

if __name__ == "__main__":
    #print(app.url_map)
    app.run(debug=True)
