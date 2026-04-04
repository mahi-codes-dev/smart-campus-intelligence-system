from flask import Flask, jsonify, request
import psycopg2
from pathlib import Path
from database import get_db_connection
from auth.auth_middleware import token_required, role_required
from config import settings
from routes.student_routes import student_bp
from auth.auth_routes import auth_bp
from routes.subject_routes import subject_bp
from routes.attendance_routes import attendance_bp
from routes.marks_routes import marks_bp
from routes.readiness_routes import readiness_bp
from routes.skills_routes import skills_bp
from routes.mock_routes import mock_bp
from routes.faculty_routes import faculty_bp
from routes.faculty_dashboard_routes import faculty_dashboard_bp
from routes.student_skill_routes import student_skill_bp
from routes.admin_dashboard_routes import admin_dashboard_bp
from routes.admin_routes import admin_bp
from routes.prediction_routes import prediction_bp
from routes.theme_routes import theme_bp
from routes.notification_routes import notification_bp
from routes.goals_routes import goals_bp
from core.security_headers import apply_security_headers
from services.attendance_service import ensure_attendance_table_consistency
from services.marks_service import ensure_marks_table_consistency
from services.mock_service import ensure_mock_tests_table_consistency
from services.skills_service import ensure_skills_table_consistency
from services.student_service import ensure_student_table_consistency, ensure_roll_number_available
from services.subject_service import ensure_subject_table_consistency
from services.goals_service import ensure_goals_tables
from services.realtime_notification_service import RealtimeNotificationService
from services.migration_service import run_migrations
# from routes.readiness_routes import get_top_students
from flask import render_template


app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
app.config["SECRET_KEY"] = settings.flask_secret_key
app.config["ENV"] = settings.flask_env
app.config["DEBUG"] = settings.flask_debug
apply_security_headers(app)

try:
    run_migrations()
    ensure_student_table_consistency()
    ensure_subject_table_consistency()
    ensure_marks_table_consistency()
    ensure_attendance_table_consistency()
    ensure_mock_tests_table_consistency()
    ensure_skills_table_consistency()
    ensure_goals_tables()
    RealtimeNotificationService.ensure_notifications_table()
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
app.register_blueprint(faculty_dashboard_bp)
app.register_blueprint(student_skill_bp)
app.register_blueprint(admin_dashboard_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(prediction_bp)
app.register_blueprint(theme_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(goals_bp)
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
@token_required
@role_required("Admin")
def create_table():
    try:
        ensure_student_table_consistency()

        return "Students table created successfully 🎯"

    except Exception as e:
        return f"Error: {e}"
    

@app.route("/add-student", methods=["POST"])
@token_required
@role_required("Admin")
def add_student():
    conn = None
    cur = None

    try:
        data = request.get_json()

        if not data or "name" not in data or "email" not in data or "department" not in data or "roll_number" not in data:
            return jsonify({"error": "Missing required fields"}), 400

        name = data["name"]
        email = data["email"]
        department = data["department"]
        roll_number = (data["roll_number"] or "").strip()

        if not roll_number:
            return jsonify({"error": "Roll number is required"}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        ensure_roll_number_available(roll_number, connection=conn)

        cur.execute("""
            INSERT INTO students (name, email, department, roll_number)
            VALUES (%s, %s, %s, %s);
        """, (name, email, department, roll_number))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Student added successfully 🎓"}), 201

    except ValueError as e:
        if conn:
            conn.rollback()
        if cur:
            cur.close()
        if conn:
            conn.close()
        return jsonify({"error": str(e)}), 400
    except psycopg2.errors.UniqueViolation:
        if conn:
            conn.rollback()
        if cur:
            cur.close()
        if conn:
            conn.close()
        return jsonify({"error": "Email already exists"}), 400
    except Exception as e:
        if conn:
            conn.rollback()
        if cur:
            cur.close()
        if conn:
            conn.close()
        return jsonify({"error": str(e)}), 500
    

@app.route("/update-student/<int:id>", methods=["PUT"])
@token_required
@role_required("Admin")
def update_student(id):
    conn = None
    cur = None

    try:
        data = request.get_json()

        name = data["name"]
        email = data["email"]
        department = data["department"]
        roll_number = (data.get("roll_number") or "").strip()

        if not roll_number:
            return jsonify({"error": "Roll number is required"}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        ensure_roll_number_available(roll_number, connection=conn, exclude_student_id=id)

        cur.execute("""
            UPDATE students
            SET name = %s,
                email = %s,
                department = %s,
                roll_number = %s
            WHERE id = %s;
        """, (name, email, department, roll_number, id))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Student updated successfully 🔄"})

    except ValueError as e:
        if conn:
            conn.rollback()
        if cur:
            cur.close()
        if conn:
            conn.close()
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        if conn:
            conn.rollback()
        if cur:
            cur.close()
        if conn:
            conn.close()
        return jsonify({"error": str(e)})
    

@app.route("/delete-student/<int:id>", methods=["DELETE"])
@token_required
@role_required("Admin")
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

@app.route('/student-profile')
def student_profile():
    return render_template('student_profile.html')

@app.route('/goals')
def goals_page():
    return render_template('goals.html')

@app.route('/notifications')
def notifications_page():
    return render_template('notifications.html')

@app.route('/admin-dashboard')
@app.route('/dashboard')
def admin_dashboard_page():
    return render_template('dashboard_admin.html')

if __name__ == "__main__":
    #print(app.url_map)
    app.run(debug=settings.flask_debug)
