from functools import wraps
from flask import request, jsonify
import jwt

SECRET_KEY = "smartcampussecret123"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from header
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None

            if "Authorization" in request.headers:
                token = request.headers["Authorization"].split(" ")[1]

            if not token:
                return jsonify({"error": "Token is missing"}), 401

            try:
                data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                user_role_id = data["role_id"]
            except:
                return jsonify({"error": "Invalid token"}), 401

            # Map role_id to role name
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