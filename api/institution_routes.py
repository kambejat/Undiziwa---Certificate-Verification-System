import secrets
from flask import flash, redirect, request, render_template, session, url_for
from .init import api
from models import Certificate, User, Verification, db, Institution
from schema.schemas import InstitutionSchema
from.helpers import login_required

institution_schema = InstitutionSchema()
institutions_schema = InstitutionSchema(many=True)

@api.route('/institutions', methods=['POST'])
def create_institution():
    # Extract form data
    institution_name = request.form.get("institution_name")
    address = request.form.get("address")
    contact_email = request.form.get("contact_email")
    contact_phone = request.form.get("contact_phone")

    # Auto-generate API URL and Token
    api_url = f"https://api.example.com/{secrets.token_hex(4)}"
    api_token = secrets.token_hex(16)

    # Create new Institution instance
    new_item = Institution(
        institution_name=institution_name,
        address=address,
        contact_email=contact_email,
        contact_phone=contact_phone,
        api_url=api_url,
        api_token=api_token
    )

    # Save to database
    db.session.add(new_item)
    db.session.commit()

    flash("Institution created successfully.", "success")

    # Redirect back to the institutions page
    return redirect(url_for("api.view_institutions"))

@api.route("/institution/dashboard", endpoint="institution_dashboard")
@login_required
def institution_dashboard():
    """
    Shows pending and completed verifications for the user's institution.
    """
    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("api.login"))

    # Get the user's institution
    inst = Institution.query.get(user.institution_id)
    if not inst:
        flash("Institution not found.", "error")
        return redirect(url_for("api.index"))

    # Pending verifications
    pending = (
        Verification.query.filter_by(status="pending")
        .join(Certificate)
        .filter(Certificate.institution_id == inst.institution_id)
        .all()
    )

    # Completed verifications
    completed = (
        Verification.query.filter(Verification.status.in_(["valid", "invalid", "not_found"]))
        .join(Certificate)
        .filter(Certificate.institution_id == inst.institution_id)
        .all()
    )

    return render_template(
        "institution_dashboard.html",
        institution=inst,   # ✅ Pass the institution object to template
        pending=pending,
        completed=completed
    )

@api.route('/institutions/<int:id>', methods=['GET'])
def get_institution(id):
    return institution_schema.jsonify(Institution.query.get_or_404(id))

@api.route('/institutions/<int:id>', methods=['PUT'])
def update_institution(id):
    item = Institution.query.get_or_404(id)
    updated = institution_schema.load(request.json, instance=item)
    db.session.commit()
    return institution_schema.jsonify(updated)

@api.route('/institutions/<int:id>', methods=['DELETE'])
def delete_institution(id):
    item = Institution.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return '', 204
