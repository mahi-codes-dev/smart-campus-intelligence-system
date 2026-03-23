from functools import wraps
from flask import request, jsonify
import jwt

SECRET_KEY = "smartcampussecret123"


# ✅ TOKEN REQUIRED (FIXED)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # 🔥 Get token from header safely
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            parts = auth_header.split(" ")

            if len(parts) == 2:
                token = parts[1]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

            # 🔥 VERY IMPORTANT: Attach user to request
            request.user = data

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