from collections import defaultdict, deque
from functools import wraps
from threading import Lock
from time import time

from flask import jsonify, request


_REQUEST_LOG = defaultdict(deque)
_RATE_LIMIT_LOCK = Lock()


def _get_client_identifier():
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"


def rate_limit(max_requests: int, window_seconds: int):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time()
            client_key = f"{func.__name__}:{_get_client_identifier()}"

            with _RATE_LIMIT_LOCK:
                history = _REQUEST_LOG[client_key]

                while history and now - history[0] >= window_seconds:
                    history.popleft()

                if len(history) >= max_requests:
                    retry_after = max(1, int(window_seconds - (now - history[0])))
                    response = jsonify(
                        {
                            "error": "Too many requests",
                            "message": "Rate limit exceeded. Please try again shortly.",
                        }
                    )
                    response.status_code = 429
                    response.headers["Retry-After"] = str(retry_after)
                    return response

                history.append(now)

            return func(*args, **kwargs)

        return wrapper

    return decorator
