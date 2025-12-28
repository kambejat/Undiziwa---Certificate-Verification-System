# utils/roles.py
from functools import wraps
from flask import session, abort

def require_roles(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            role = session.get("role")
            if role not in allowed_roles:
                abort(403, "Forbidden")
            return func(*args, **kwargs)
        return wrapper
    return decorator
