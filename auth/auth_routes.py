from flask import Blueprint, request, jsonify
from database import get_db_connection
import bcrypt
import jwt
import datetime
from services.student_service import ensure_student_table_consistency, sync_student_record

auth_bp = Blueprint("auth_bp", __name__)


def _get_dashboard_path(role_name):
    role_to_path = {
        "student": "/student-dashboard",
        "faculty": "/faculty-dashboard",
        "admin": "/dashboard",
    }

    return role_to_path.get((role_name or "").lower(), "/")


def _get_roles():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, role_name
        FROM roles
        ORDER BY id ASC
        """
    )
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "dashboard_path": _get_dashboard_path(row[1]),
        }
        for row in rows
    ]


@auth_bp.route("/auth/roles", methods=["GET"])
def get_roles():
    try:
        return jsonify(_get_roles()), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/register", methods=["POST"])
@auth_bp.route("/auth/register", methods=["POST"])
def register():
    try:
        data = request.get_json() or {}
        print("REGISTER_REQUEST:", data)

        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()
        password = data.get("password") or ""
        department = (data.get("department") or "").strip()

        try:
            role_id = int(data.get("role_id"))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid role selected"}), 400

        if not name or not email or not password or not role_id:
            return jsonify({"error": "Missing fields"}), 400

        if role_id == 3 and not department:
            return jsonify({"error": "Department is required for student registration"}), 400

        ensure_student_table_consistency()

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": "Email already registered"}), 400

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

        cur.execute("""
            INSERT INTO users (name, email, password, role_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, (name, email, hashed_password, role_id))

        user_id = cur.fetchone()[0]

        if role_id == 3:
            sync_student_record(user_id, name, email, department, connection=conn)

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "message": "User registered successfully",
            "user": {
                "id": user_id,
                "name": name,
                "email": email,
                "role_id": role_id,
                "department": department or None,
            }
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}
        print("LOGIN_REQUEST:", data)

        email = (data.get("email") or "").strip()
        password = data.get("password") or ""

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT u.id, u.name, u.email, u.password, u.role_id, r.role_name
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE LOWER(u.email) = LOWER(%s)
            """,
            (email,),
        )
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user is None:
            return jsonify({"error": "User not found"}), 404

        stored_password = user[3]

        if not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            return jsonify({"error": "Invalid password"}), 401

        token = jwt.encode({
            "user_id": user[0],
            "email": user[2],
            "role_id": user[4],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }, "smartcampussecret123", algorithm="HS256")

        role_name = user[5] or ""
        dashboard_path = _get_dashboard_path(role_name)

        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user[0],
                "name": user[1],
                "email": user[2],
                "role_id": user[4],
                "role_name": role_name,
                "dashboard_path": dashboard_path,
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
