import inspect
import os
from functools import wraps

from flask import g, jsonify, request
import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET is not configured in environment variables")

if not JWT_ALGORITHM:
    raise RuntimeError("JWT_ALGORITHM is not configured in environment variables")


ROLE_MAP = {
    1: "Admin",
    2: "Faculty",
    3: "Student",
}


def _build_current_user(payload):
    role_name = ROLE_MAP.get(payload.get("role_id"), "Unknown")
    return {
        **payload,
        "id": payload.get("user_id"),
        "user_id": payload.get("user_id"),
        "role": role_name,
        "role_name": role_name,
    }

def token_required(f):
    signature = inspect.signature(f)
    expects_current_user = "current_user" in signature.parameters

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
            current_user = _build_current_user(payload)
            data = current_user
            request.user_id = current_user.get("user_id")
            g.user = current_user
            g.user_id = current_user.get("user_id")
            g.user_role = current_user.get("role")
            request.user = data   # ✅ ADD THIS LINE
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        if expects_current_user and "current_user" not in kwargs:
            kwargs["current_user"] = request.user  # type: ignore[attr-defined]

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

            user_role = request.user.get("role_name") or ROLE_MAP.get(request.user.get("role_id"))

            # 🔥 Map role_id → role name

            if user_role != required_role:
                return jsonify({"error": "Access denied"}), 403

            return f(*args, **kwargs)

        return decorated
    return decorator
