from flask import (
    request, render_template, jsonify,
    session, flash, redirect, url_for,
)
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from config import Config
from .init import api
from models import db, Verification, Certificate, Institution, User
from utils.email_service import send_email
from schema.schemas import VerificationSchema

# ============================================================
# Schemas
# ============================================================
verification_schema = VerificationSchema()
verifications_schema = VerificationSchema(many=True)


# ============================================================
# Background Verification Job
# ============================================================
def run_verification_job(verification_id):
    ver = Verification.query.get(verification_id)
    if not ver:
        return

    cert = Certificate.query.get(ver.certificate_id)

    if cert:
        ver.status = "valid"
        ver.result_json = '{"verified": true}'
        cert.verified = True
    else:
        ver.status = "not_found"
        ver.result_json = '{"verified": false}'

    ver.verified_at = datetime.utcnow()
    db.session.commit()


# ============================================================
# Create Verification Request
# ============================================================
@api.route('/verifications/request', methods=['POST'])
def request_verification():
    # --- Collect form data ---
    student_name = request.form.get('student_name', '').strip()
    student_number = request.form.get('student_number', '').strip()
    course_name = request.form.get('course_name', '').strip()
    graduation_year = request.form.get('graduation_year')
    institution_id = request.form.get('institution_id')
    message = request.form.get('message', '').strip()
    file = request.files.get('certificate_file')  # <-- uploaded file
    user_id = session.get("user_id")

    # --- Validate required fields ---
    if not all([student_name, course_name, graduation_year, institution_id]):
        flash("All required fields must be filled.", "error")
        return redirect(url_for("api.view_verifications"))

    # --- Load institution ---
    inst = Institution.query.get_or_404(institution_id)

    # --- Handle file upload ---
    file_path = None
    if file and file.filename != "":
        filename = secure_filename(file.filename)
        upload_folder = Config.UPLOAD_FOLDER

        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
   

    # --- Create certificate ---
    cert = Certificate(
        student_name=student_name,
        student_number=student_number,
        course_name=course_name,
        graduation_year=int(graduation_year),
        uploaded_by=user_id,
        institution_id=inst.institution_id,
        certificate_file=file_path  # <-- store path
    )
    db.session.add(cert)
    db.session.commit()

    # --- Create verification record ---
    verification = Verification(
        certificate_id=cert.certificate_id,
        requested_by=user_id,
        verified_by_institution_id=inst.institution_id,
        status="pending",
        method="manual_form",
        requested_at=datetime.utcnow()
    )
    db.session.add(verification)
    db.session.commit()

    # --- Build verification link ---
    verification_url = url_for(
        "api.view_verification",
        verification_id=verification.verification_id,
        _external=True
    )

    # --- Send email ---
    if inst.contact_email:
        send_email(
            to=inst.contact_email,
            subject="Certificate Verification Request",
            body=f"""
            A certificate verification request has been submitted.<br><br>
            <b>Student:</b> {cert.student_name}<br>
            <b>Student Number:</b> {cert.student_number}<br>
            <b>Course:</b> {cert.course_name}<br>
            <b>Year:</b> {cert.graduation_year}<br><br>
            <a href="{verification_url}">Click here to verify</a><br><br>
            <b>Message:</b><br>{message or 'No message'}
            """
        )

    flash("Certificate sent for verification successfully!", "success")
    return redirect(url_for("api.view_verifications"))

# ============================================================
# Manual Trigger
# ============================================================
@api.route('/verifications/run/<int:verification_id>', methods=['POST'])
def run_now(verification_id):
    run_verification_job(verification_id)
    return jsonify({"message": "Verification executed."}), 200


# ============================================================
# Delete Verification
# ============================================================
@api.route('/verifications/<int:verification_id>', methods=['DELETE'])
def delete_verification(verification_id):
    ver = Verification.query.get_or_404(verification_id)
    db.session.delete(ver)
    db.session.commit()
    return '', 204


# ============================================================
# View & Handle Manual Verification
# ============================================================
@api.route('/verifications/view/<int:verification_id>', methods=['GET', 'POST'])
def view_verification(verification_id):
    if "user_id" not in session:
        flash("Please log in to verify certificates.", "error")
        return redirect(url_for("api.login"))

    user = User.query.get(session["user_id"])
    if not user:
        flash("Unauthorized access.", "error")
        return redirect(url_for("api.login"))

    ver = Verification.query.get_or_404(verification_id)
    cert = Certificate.query.get(ver.certificate_id)

    if not cert:
        flash("Certificate not found.", "error")
        return redirect(url_for("api.index"))

    if cert.institution_id != user.institution_id:
        flash("You do not have permission to verify this certificate.", "error")
        return redirect(url_for("api.index"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "valid":
            ver.status = "valid"
            ver.result_json = '{"verified": true}'
            cert.verified = True
        elif action == "invalid":
            ver.status = "invalid"
            ver.result_json = '{"verified": false}'

        ver.verified_at = datetime.utcnow()
        db.session.commit()

        return render_template("verification_success.html", verification=ver)

    return render_template(
        "verify_certificate.html",
        verification=ver,
        certificate=cert,
        user=user
    )


# ============================================================
# View Verification Page (Form + Institutions)
# ============================================================
@api.route('/verifications', endpoint="verifications_page")
def view_verifications():
    institutions = Institution.query.all()
    print(institutions)
    return render_template(
        "verifications.html",
        institutions=institutions
    )

@api.route('/institutions/json')
def institutions_json():
    institutions = Institution.query.all()
    return jsonify([
        {"id": inst.institution_id, "name": inst.institution_name, "email": inst.contact_email}
        for inst in institutions
    ])

# ============================================================
# Send Reminder Email
# ============================================================
@api.route('/verifications/remind/<int:verification_id>', methods=['POST'])
def send_verification_reminder(verification_id):
    ver = Verification.query.get_or_404(verification_id)
    cert = Certificate.query.get_or_404(ver.certificate_id)
    inst = Institution.query.get_or_404(ver.verified_by_institution_id)

    # Build verification link
    verification_url = url_for(
        "api.view_verification",
        verification_id=ver.verification_id,
        _external=True
    )

    # Send reminder email
    if inst.contact_email:
        send_email(
            to=inst.contact_email,
            subject="Reminder: Certificate Verification Pending",
            body=f"""
            <b>Reminder:</b> A certificate verification is still pending.<br><br>
            <b>Student:</b> {cert.student_name}<br>
            <b>Student Number:</b> {cert.student_number}<br>
            <b>Course:</b> {cert.course_name}<br>
            <b>Year:</b> {cert.graduation_year}<br><br>

            <a href="{verification_url}">Click here to verify</a>
            """
        )

    return jsonify({"message": "Reminder sent successfully!"}), 200
