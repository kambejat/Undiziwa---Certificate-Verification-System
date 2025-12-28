from flask import redirect, request, url_for, session, flash, render_template
from .init import api
from .helpers import login_required
from models import Institution, User, Certificate, Verification
from schema.schemas import UserSchema 

user_schema = UserSchema()
users_schema = UserSchema(many=True)

@api.route('/')
@login_required
def index():
    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found", "error")
        return redirect(url_for("api.login"))

    # Redirect institution users to their dashboard
    if user.institution_id:
        return redirect(url_for("api.institution_dashboard"))

    # Otherwise, show a generic dashboard
    return render_template('index.html', username=session.get("username"))

@api.route('/institutions/view')
@login_required
def view_institutions():
    items = Institution.query.all()
    return render_template('institutions.html', institutions=items)

@api.route("/users/view", methods=["GET"])
@login_required
def view_users():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    pagination = User.query.order_by(User.user_id).paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items
    serialized = users_schema.dump(items) if items else []
    
    return render_template(
        "users.html",
        users=serialized,
        current_user_role=session.get("user_role")
    )

@api.route('/certificates/view')
@login_required
def view_certificates():
    certificates = Certificate.query.all()
    if not certificates:
        flash("No certificates available.", "info")
    return render_template('certificates.html', certificates=certificates)


@api.route('/verifications/view')
@login_required
def view_verifications():
    items = Verification.query.all()
    return render_template('verifications.html', verifications=items)

