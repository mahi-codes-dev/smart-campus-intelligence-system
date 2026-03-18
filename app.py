from flask import Flask, jsonify, request
import psycopg2
import os
from dotenv import load_dotenv
from database import get_db_connection
from routes.student_routes import student_bp
from auth.auth_routes import auth_bp
from routes.subject_routes import subject_bp
from routes.attendance_routes import attendance_bp

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.register_blueprint(student_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(subject_bp)
app.register_blueprint(attendance_bp)

@app.route("/")
def home():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({"message": "Secure Database Connected Successfully 🔐"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

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
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100) UNIQUE,
                department VARCHAR(100)
            );
        """)

        conn.commit()
        cur.close()
        conn.close()

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

if __name__ == "__main__":
    app.run(debug=True)