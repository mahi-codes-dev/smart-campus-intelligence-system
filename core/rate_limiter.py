"""
Simple in-memory rate limiter.

Supports per-IP, sliding-window rate limiting without external dependencies.
Use the @rate_limit decorator on Flask routes.
"""
import time
import threading
from functools import wraps
from collections import defaultdict, deque
from flask import request, jsonify


class RateLimiter:
    """Thread-safe sliding-window rate limiter backed by an in-memory store."""

    def __init__(self):
        self._store: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """
        Check whether `key` is within its rate limit.

        Returns:
            (allowed: bool, retry_after: int)  – retry_after is seconds to wait when blocked.
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            dq = self._store[key]

            # Drop timestamps outside the window
            while dq and dq[0] < cutoff:
                dq.popleft()

            if len(dq) < max_requests:
                dq.append(now)
                return True, 0

            # Blocked: tell the caller when the oldest request will age out
            retry_after = int(dq[0] - cutoff) + 1
            return False, retry_after

    def clear(self, key: str):
        with self._lock:
            self._store.pop(key, None)


# Module-level singleton
_limiter = RateLimiter()


def rate_limit(max_requests: int = 60, window_seconds: int = 60, per: str = "ip"):
    """
    Decorator factory.  Apply to Flask route functions.

    Args:
        max_requests:    Maximum calls allowed in the window.
        window_seconds:  Sliding-window size in seconds.
        per:             Grouping key – ``"ip"`` (default) or ``"global"``.

    Example::

        @app.route("/api/login", methods=["POST"])
        @rate_limit(max_requests=5, window_seconds=60)
        def login():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if per == "ip":
                client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
                key = f"{f.__name__}:{client_ip}"
            else:
                key = f"global:{f.__name__}"

            allowed, retry_after = _limiter.is_allowed(key, max_requests, window_seconds)

            if not allowed:
                response = jsonify({
                    "success": False,
                    "error": "Too many requests. Please slow down.",
                    "retry_after": retry_after,
                })
                response.status_code = 429
                response.headers["Retry-After"] = str(retry_after)
                response.headers["X-RateLimit-Limit"] = str(max_requests)
                response.headers["X-RateLimit-Window"] = str(window_seconds)
                return response

            return f(*args, **kwargs)
        return wrapper
    return decorator
