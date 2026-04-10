import logging
from pathlib import Path
import psycopg2
from flask import Flask, jsonify, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from auth.auth_middleware_replacement import token_required, role_required
from auth.auth_routes import auth_bp
from config import settings
from core.logging_config import configure_logging
from core.security_headers import apply_security_headers
from database import get_db_connection
from routes.admin_dashboard_routes import admin_dashboard_bp
from routes.admin_routes import admin_bp
from routes.attendance_routes import attendance_bp
from routes.faculty_dashboard_routes import faculty_dashboard_bp
from routes.faculty_routes import faculty_bp
from routes.goals_routes import goals_bp
from routes.marks_routes import marks_bp
from routes.mock_routes import mock_bp
from routes.prediction_routes import prediction_bp
from routes.notification_routes import notification_bp
from routes.readiness_routes import readiness_bp
from routes.skills_routes import skills_bp
from routes.student_routes import student_bp
from routes.student_skill_routes import student_skill_bp
from routes.subject_routes import subject_bp
from routes.theme_routes import theme_bp
from services.attendance_service import ensure_attendance_table_consistency
from services.faculty_dashboard_service import ensure_intervention_table_consistency
from services.goals_service import ensure_goals_tables
from services.marks_service import ensure_marks_table_consistency
from services.migration_service import run_migrations
from services.mock_service import ensure_mock_tests_table_consistency
from services.realtime_notification_service import RealtimeNotificationService
from services.skills_service import ensure_skills_table_consistency
from services.student_service import ensure_student_table_consistency, ensure_roll_number_available
from services.subject_service import ensure_subject_table_consistency
from services.theme_service import ThemeService
from utils.validators import RequestValidator

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
app.config["SECRET_KEY"] = settings.flask_secret_key
app.config["ENV"] = settings.flask_env
app.config["DEBUG"] = settings.flask_debug
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = settings.auth_cookie_secure
app.config["SESSION_COOKIE_SAMESITE"] = settings.auth_cookie_samesite

if settings.trust_proxy_count > 0:
    app.wsgi_app = ProxyFix(  # type: ignore[assignment]
        app.wsgi_app,
        x_for=settings.trust_proxy_count,
        x_proto=settings.trust_proxy_count,
        x_host=settings.trust_proxy_count,
    )

apply_security_headers(app)

startup_status = {
    "ready": False,
    "database": "unknown",
    "bootstrap_error": None,
}

try:
    run_migrations()
    ensure_student_table_consistency()
    ensure_subject_table_consistency()
    ensure_marks_table_consistency()
    ensure_attendance_table_consistency()
    ensure_mock_tests_table_consistency()
    ensure_skills_table_consistency()
    ensure_goals_tables()
    ensure_intervention_table_consistency()
    RealtimeNotificationService.ensure_notifications_table()
    ThemeService.ensure_theme_table()
    startup_status["ready"] = True
    startup_status["database"] = "connected"
except Exception as schema_error:
    startup_status["database"] = "disconnected"
    startup_status["bootstrap_error"] = str(schema_error)
    logger.exception("Application bootstrap failed")
    if settings.strict_startup_validation:
        raise

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


@app.route("/offline")
def offline_page():
    return render_template("offline.html")


@app.route("/health/live")
def live_check():
    return jsonify({"status": "alive", "app": settings.app_name}), 200
    # try:
    #     conn = get_db_connection()
    #     conn.close()
    #     return jsonify({"message": "Secure Database Connected Successfully 🔐"}), 200
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500

@app.route("/health/ready")
@app.route("/health")
def health_check():
    status = dict(startup_status)

    try:
        conn = get_db_connection()
        conn.close()
        status["database"] = "connected"
    except Exception as e:
        status["database"] = "disconnected"
        status["ready"] = False
        status["bootstrap_error"] = status.get("bootstrap_error") or str(e)

    status["status"] = "healthy" if status.get("ready") else "unhealthy"
    return jsonify(status), 200 if status["status"] == "healthy" else 503

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
        data = request.get_json() or {}
        v = RequestValidator(data)
        v.required("name", "email", "department", "roll_number").sanitize("name", 100).email("email").sanitize("department", 100).roll_number("roll_number")
        if v.has_errors():
            return jsonify({"error": v.first_error()}), 400
        name = v.validated_data["name"]
        email = v.validated_data["email"]
        department = v.validated_data["department"]
        roll_number = v.validated_data["roll_number"]

        conn = get_db_connection()
        cur = conn.cursor()
        ensure_roll_number_available(roll_number, connection=conn)

        cur.execute("""
            INSERT INTO students (name, email, department, roll_number)
            VALUES (%s, %s, %s, %s);
        """, (name, email, department, roll_number))

        conn.commit()

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
        data = request.get_json() or {}
        v = RequestValidator(data)
        v.required("name", "email", "department", "roll_number").sanitize("name", 100).email("email").sanitize("department", 100).roll_number("roll_number")
        if v.has_errors():
            return jsonify({"error": v.first_error()}), 400
        name = v.validated_data["name"]
        email = v.validated_data["email"]
        department = v.validated_data["department"]
        roll_number = v.validated_data["roll_number"]

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
