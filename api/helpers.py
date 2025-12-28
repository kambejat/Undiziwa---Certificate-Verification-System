from functools import wraps
from flask import session, redirect, url_for, flash
from marshmallow import ValidationError

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("api.login"))
        return func(*args, **kwargs)
    return wrapper

def enforce_institution_scope(payload):
    role = session.get("role")
    session_institution = session.get("institution_id")

    # Institution admins & HR are locked
    if role in ["institution_admin", "hr"]:
        payload["institution_id"] = session_institution

    # Super admins: trust payload (optional validation)
    elif role == "super_admin":
        if not payload.get("institution_id"):
            raise ValidationError("Institution is required for this user")

    # Gov admins: allow but fallback if missing
    elif role == "gov_admin":
        payload["institution_id"] = payload.get("institution_id") or session_institution

    return payload

