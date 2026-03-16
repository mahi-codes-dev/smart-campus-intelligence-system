from flask import Blueprint, request, jsonify
from database import get_db_connection
import psycopg2
import bcrypt

auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        name = data["name"]
        email = data["email"]
        password = data["password"]
        role_id = data["role_id"]

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO users (name, email, password, role_id)
        VALUES (%s, %s, %s, %s)
        """, (name, email, hashed_password, role_id))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500