from flask import redirect, render_template, request, jsonify, send_from_directory, flash, url_for
from marshmallow import ValidationError
from werkzeug.exceptions import NotFound
import os

from .init import api
from .helpers import login_required
from models import db, Certificate
from schema.schemas import CertificateSchema

UPLOAD_FOLDER = "static/uploads/certificates"   # adjust path as needed

certificate_schema = CertificateSchema()
certificates_schema = CertificateSchema(many=True)


# -------------------------------
# CREATE CERTIFICATE
# -------------------------------
@api.route('/certificates', methods=['POST'])
def create_certificate():
    try:
        new_item = certificate_schema.load(request.json)
        db.session.add(new_item)
        db.session.commit()
        return certificate_schema.jsonify(new_item), 201

    except ValidationError as err:
        return jsonify({"error": "Invalid data", "details": err.messages}), 400

    except Exception as e:
        return jsonify({"error": "Server error", "message": str(e)}), 500


# -------------------------------
# GET ALL CERTIFICATES
# -------------------------------
@api.route('/certificates', methods=['GET'])
def get_certificates():
    try:
        return certificates_schema.jsonify(Certificate.query.all()), 200
    except Exception as e:
        return jsonify({"error": "Server error", "message": str(e)}), 500


# -------------------------------
# GET SINGLE CERTIFICATE
# -------------------------------
@api.route('/certificates/<int:id>', methods=['GET'])
def get_certificate(id):
    try:
        cert = Certificate.query.get_or_404(id)
        return certificate_schema.jsonify(cert), 200

    except NotFound:
        return jsonify({"error": "Certificate not found"}), 404

    except Exception as e:
        return jsonify({"error": "Server error", "message": str(e)}), 500


# -------------------------------
# UPDATE CERTIFICATE
# -------------------------------
@api.route('/certificates/<int:id>', methods=['PUT'])
def update_certificate(id):
    try:
        item = Certificate.query.get_or_404(id)
        updated = certificate_schema.load(request.json, instance=item)
        db.session.commit()
        return certificate_schema.jsonify(updated), 200

    except ValidationError as err:
        return jsonify({"error": "Invalid data", "details": err.messages}), 400

    except NotFound:
        return jsonify({"error": "Certificate not found"}), 404

    except Exception as e:
        return jsonify({"error": "Server error", "message": str(e)}), 500


# -------------------------------
# DELETE CERTIFICATE
# -------------------------------
@api.route('/certificates/<int:id>', methods=['DELETE'])
def delete_certificate(id):
    try:
        item = Certificate.query.get_or_404(id)

        # delete certificate file if exists
        if item.certificate_file:
            file_path = os.path.join(UPLOAD_FOLDER, item.certificate_file)
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(item)
        db.session.commit()
        return '', 204

    except NotFound:
        return jsonify({"error": "Certificate not found"}), 404

    except Exception as e:
        return jsonify({"error": "Server error", "message": str(e)}), 500


# -------------------------------
# DOWNLOAD CERTIFICATE FILE
# -------------------------------
@api.route('/certificates/<int:id>/download', methods=['GET'])
def download_certificate_file(id):
    try:
        cert = Certificate.query.get_or_404(id)

        if not cert.certificate_file:
            return jsonify({"error": "This certificate has no file attached"}), 404

        filepath = os.path.join(UPLOAD_FOLDER, cert.certificate_file)

        if not os.path.exists(filepath):
            return jsonify({"error": "File not found on server"}), 404

        filename = cert.certificate_file
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

    except NotFound:
        return jsonify({"error": "Certificate not found"}), 404

    except Exception as e:
        return jsonify({"error": "Server error", "message": str(e)}), 500

UPLOAD_FOLDER = "uploads"  # your folder outside static

@api.route('/certificates/<int:id>/download', methods=['GET'])
@login_required
def download_certificate(id):
    cert = Certificate.query.get(id)
    if not cert:
        flash("Certificate not found.", "danger")
        return redirect(url_for('api.view_certificates'))

    if not cert.certificate_file:
        flash("This certificate has no file attached.", "danger")
        return redirect(url_for('api.view_certificates'))

    file_path = os.path.join(UPLOAD_FOLDER, cert.certificate_file)
    if not os.path.exists(file_path):
        flash("File missing from server.", "danger")
        return redirect(url_for('api.view_certificates'))

    # send file from uploads folder
    return send_from_directory(UPLOAD_FOLDER, cert.certificate_file, as_attachment=True)


@api.route("/search-certificates-html")
@login_required
def search_certificates_html():
    query = request.args.get("q", "").strip().lower()
    
    if not query:
        return ""

    results = Certificate.query.filter(
        db.or_(
            db.func.lower(Certificate.student_name).like(f"%{query}%"),
            db.func.lower(Certificate.certificate_id).like(f"%{query}%"),
            db.func.lower(Certificate.course_name).like(f"%{query}%")
        )
    ).limit(20).all()

    return render_template("partials/certificate_cards.html", certificates=results)
