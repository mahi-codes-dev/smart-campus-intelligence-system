import token

from flask import Blueprint, request, jsonify
from database import get_db_connection
import psycopg2
import bcrypt
import jwt
import datetime

auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        name = data["name"]
        email = data["email"]
        password = data["password"]
        role_id = data["role_id"]

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

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

@auth_bp.route("/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        email = data["email"]
        password = data["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id, name, email, password, role_id FROM users WHERE email = %s", (email,))
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

        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user[0],
                "name": user[1],
                "email": user[2],
                "role_id": user[4]
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500