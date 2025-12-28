from sqlalchemy.orm import validates
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Institution(db.Model):
    __tablename__ = 'institutions'
    institution_id = db.Column(db.Integer, primary_key=True)
    institution_name = db.Column(db.String(255))
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    api_url = db.Column(db.Text)
    api_token = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    address = db.Column(db.String(255))


class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.Text)
    role = db.Column(db.Enum('hr', 'institution_admin', 'gov_admin', 'super_admin', name='user_roles'))
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.institution_id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    target_user_id = db.Column(db.Integer, nullable=True)   
    action = db.Column(db.String(100), nullable=False)      
    performed_by = db.Column(db.String(100), nullable=True) 
    meta = db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

    def is_expired(self):
        return datetime.utcnow() > self.expires_at



class Certificate(db.Model):
    __tablename__ = 'certificates'
    certificate_id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100))
    student_number = db.Column(db.String(50))
    course_name = db.Column(db.String(100))
    graduation_year = db.Column(db.Integer)

    # Store path to uploaded certificate
    certificate_file = db.Column(db.String(200))  # path like 'uploads/certificates/file.pdf'

    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.institution_id'))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    verified = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Verification(db.Model):
    __tablename__ = 'verifications'
    verification_id = db.Column(db.Integer, primary_key=True)

    certificate_id = db.Column(
        db.Integer,
        db.ForeignKey('certificates.certificate_id'),
        nullable=True
    )

    # user who requested verification (optional)
    requested_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))

    # the institution that must confirm
    verified_by_institution_id = db.Column(
        db.Integer,
        db.ForeignKey('institutions.institution_id')
    )

    status = db.Column(
        db.Enum('valid', 'invalid', 'pending', 'not_found', name='verification_status'),
        default='pending'
    )

    method = db.Column(
        db.Enum('manual_form', 'student_number', 'scan_upload', name='verification_method'),
        default='manual_form'
    )

    # file uploaded by user for verification
    verification_file = db.Column(db.Text)  

    result_json = db.Column(db.Text)

    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)

    certificate = db.relationship("Certificate", backref="verifications")
