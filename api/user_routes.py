# routes/users.py
import secrets
import string
from datetime import datetime, timedelta

from flask import (
    flash, redirect, request, session, abort, render_template,
    url_for, current_app, jsonify
)

from itsdangerous import URLSafeTimedSerializer

from .init import api
from models import db, User, PasswordResetToken
from schema.schemas import UserSchema
from .helpers import login_required, enforce_institution_scope
from utils.roles import require_roles
from utils.audit import log_audit
from utils.email_service import send_email


user_schema = UserSchema()
users_schema = UserSchema(many=True)


# --------------------------
# Helpers
# --------------------------
def generate_secure_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_-+="
    return ''.join(secrets.choice(chars) for _ in range(length))


def get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

def wants_json():
    return request.is_json or request.headers.get("Accept") == "application/json"



# --------------------------
# List users
# --------------------------
@api.route("/users", methods=["GET"])
@login_required
def api_get_users():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    search = request.args.get("search", "").strip()
    role = request.args.get("role")
    is_active = request.args.get("is_active")

    query = User.query

    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            db.or_(
                db.func.lower(User.username).like(like),
                db.func.lower(User.email).like(like)
            )
        )

    if role:
        query = query.filter(User.role == role)

    if is_active in ("true", "false"):
        query = query.filter(User.is_active == (is_active == "true"))

    pagination = query.order_by(User.user_id).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "users": users_schema.dump(pagination.items),
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages
    })


# --------------------------
# Create user + invite email
# --------------------------
@api.route("/users", methods=["POST"])
@login_required
def create_user():
    try:
        payload = enforce_institution_scope(request.json or {})
        user = user_schema.load(payload)

        user.set_password(generate_secure_password())
        db.session.add(user)
        db.session.commit()

        serializer = get_serializer()
        token = serializer.dumps({"user_id": user.user_id})

        prt = PasswordResetToken(
            user_id=user.user_id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(prt)
        db.session.commit()

        reset_link = (
            f"{request.host_url.rstrip('/')}"
            f"{url_for('api.reset_password_form')}?token={token}"
        )

        send_email(
            to=user.email,
            subject="You have been invited – Set your password",
            body=f"""
            <p>Hello <b>{user.username}</b>,</p>
            <p>An account has been created for you.</p>
            <p><a href="{reset_link}">Set your password</a></p>
            <p>This link expires in 24 hours.</p>
            """
        )

        log_audit(
            action="create_user_invite",
            target_user_id=user.user_id,
            performed_by=session.get("username"),
            meta={"institution_id": user.institution_id}
        )

        if wants_json():
            return user_schema.jsonify(user), 201

        flash("User created and invitation email sent.", "success")
        return redirect(url_for("api.api_get_users"))

    except Exception as e:
        db.session.rollback()

        if wants_json():
            return {"error": str(e)}, 400

        flash(f"Failed to create user: {str(e)}", "danger")
        return redirect(request.referrer or "/")

# --------------------------
# Update permissions
# --------------------------
@api.route("/users/<int:id>/permission", methods=["PUT"])
@login_required
@require_roles("gov_admin", "super_admin")
def update_permission(id):
    user = User.query.get_or_404(id)

    if "role" in request.json:
        user.role = request.json["role"]

    if "is_active" in request.json:
        user.is_active = request.json["is_active"]

    db.session.commit()

    log_audit(
        action="update_permission",
        target_user_id=user.user_id,
        performed_by=session.get("username")
    )

    return user_schema.jsonify(user)


# --------------------------
# Admin reset password email
# --------------------------
@api.route("/users/<int:id>/reset-password", methods=["PATCH"])
@login_required
@require_roles("gov_admin", "super_admin")
def admin_reset_password(id):
    try:
        user = User.query.get_or_404(id)

        serializer = get_serializer()
        token = serializer.dumps({"user_id": user.user_id})

        prt = PasswordResetToken(
            user_id=user.user_id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.session.add(prt)
        db.session.commit()

        reset_link = (
            f"{request.host_url.rstrip('/')}"
            f"{url_for('api.reset_password_form')}?token={token}"
        )

        send_email(
            to=user.email,
            subject="Password reset",
            body=f"""
            <p><a href="{reset_link}">Reset your password</a></p>
            <p>This link expires in 1 hour.</p>
            """
        )

        log_audit(
            action="admin_trigger_reset",
            target_user_id=user.user_id,
            performed_by=session.get("username")
        )

        if wants_json():
            return {"msg": "Reset email sent"}, 200

        flash("Password reset email sent successfully.", "success")
        return redirect(request.referrer or "/")

    except Exception as e:
        db.session.rollback()

        if wants_json():
            return {"error": str(e)}, 400

        flash(f"Failed to send reset email: {str(e)}", "danger")
        return redirect(request.referrer or "/")

# --------------------------
# Confirm reset
# --------------------------
@api.route("/reset-password/confirm", methods=["POST"])
def reset_password_confirm():
    token = request.json.get("token") if request.is_json else request.form.get("token")
    password = request.json.get("password") if request.is_json else request.form.get("password")

    prt = PasswordResetToken.query.filter_by(
        token=token, used=False
    ).first()

    if not prt or prt.is_expired():
        if wants_json():
            abort(400, "Invalid or expired token")

        flash("Invalid or expired reset link.", "danger")
        return redirect("/login")

    user = User.query.get_or_404(prt.user_id)
    user.set_password(password)
    prt.used = True

    db.session.commit()

    log_audit("reset_password_confirm", user.user_id, None)

    if wants_json():
        return {"msg": "Password reset successful"}, 200

    flash("Password reset successful. You may now log in.", "success")
    return redirect("/login")

# --------------------------
# Public reset form
# --------------------------
@api.route("/reset-password", methods=["GET"])
def reset_password_form():
    token = request.args.get("token")
    if not token:
        abort(400, "Missing token")

    return render_template("reset_password.html", token=token)
