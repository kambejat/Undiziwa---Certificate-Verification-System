from flask_marshmallow import Marshmallow
from marshmallow import fields
from marshmallow_sqlalchemy import auto_field
from models import Institution, User, Certificate, Verification

ma = Marshmallow()

class InstitutionSchema(ma.Schema):
    institution_id = fields.Int(dump_only=True)
    institution_name = fields.Str(required=True)
    address = fields.Str(required=True)
    contact_email = fields.Email()
    contact_phone = fields.Str()
    api_url = fields.Str(dump_only=True)    
    api_token = fields.Str(dump_only=True)  
    
    class Meta:
        model = Institution
        include_relationships = True
        load_instance = True

class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True  # include foreign keys like institution_id

    user_id = auto_field()
    username = auto_field(required=True)
    full_name = auto_field()
    email = auto_field()
    phone = auto_field()
    role = auto_field()
    institution_id = auto_field()
    is_active = auto_field()
    created_at = auto_field(dump_only=True)  

    # Add password field separately (write-only)
    password = fields.String(load_only=True)


class CertificateSchema(ma.Schema):
    class Meta:
        model = Certificate
        include_fk = True
        load_instance = True

class VerificationSchema(ma.Schema):
    class Meta:
        model = Verification
        include_fk = True
        load_instance = True