from functools import wraps
import os
from flask import request, jsonify
import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET is not configured in environment variables")

if not JWT_ALGORITHM:
    raise RuntimeError("JWT_ALGORITHM is not configured in environment variables")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
            request.user = data   # ✅ ADD THIS LINE
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated

# ✅ ROLE REQUIRED (UPDATED TO USE request.user)
def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):

            # 🔥 Ensure token_required runs first
            if not hasattr(request, "user"):
                return jsonify({"error": "Unauthorized"}), 401

            user_role_id = request.user.get("role_id")

            # 🔥 Map role_id → role name
            role_map = {
                1: "Admin",
                2: "Faculty",
                3: "Student"
            }

            user_role = role_map.get(user_role_id)

            if user_role != required_role:
                return jsonify({"error": "Access denied"}), 403

            return f(*args, **kwargs)

        return decorated
    return decorator
