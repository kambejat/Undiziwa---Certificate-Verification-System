import sys
from datetime import datetime
from app import create_app, db
from models import User, Institution
from werkzeug.security import generate_password_hash

app = create_app()
app.app_context().push()

def create_institution_if_not_exists(name="Default Institution", email="default@inst.com", phone="0000000000"):
    institution = Institution.query.filter_by(institution_name=name).first()
    if institution:
        print(f"Institution '{name}' already exists with ID {institution.institution_id}.")
    else:
        institution = Institution(
            institution_name=name,
            contact_email=email,
            contact_phone=phone,
            api_url="",
            api_token="",
            is_active=True
        )
        db.session.add(institution)
        db.session.commit()
        print(f"Institution '{name}' created with ID {institution.institution_id}.")
    return institution

def create_user(username, full_name, email, phone, password, role, institution_id=None, is_active=True):
    valid_roles = ('hr', 'institution_admin', 'gov_admin', 'super_admin')
    if role not in valid_roles:
        print(f"Invalid role '{role}'. Valid roles: {valid_roles}")
        return

    # Check for existing user by email or username
    if User.query.filter_by(email=email).first():
        print(f"User with email '{email}' already exists.")
        return
    if User.query.filter_by(username=username).first():
        print(f"User with username '{username}' already exists.")
        return

    # Validate institution
    if institution_id:
        institution = Institution.query.get(institution_id)
        if not institution:
            print(f"Institution with id {institution_id} not found.")
            return
    else:
        institution = create_institution_if_not_exists()
        institution_id = institution.institution_id

    # Create user
    user = User(
        username=username,
        full_name=full_name,
        email=email,
        phone=phone,
        password_hash=generate_password_hash(password),
        role=role,
        institution_id=institution_id,
        is_active=is_active,
        created_at=datetime.utcnow()
    )

    db.session.add(user)
    db.session.commit()
    print(f"User '{full_name}' ({username}) with role '{role}' created successfully.")

if __name__ == '__main__':
    if len(sys.argv) < 7:
        print("Usage: python create_user.py <username> <full_name> <email> <phone> <password> <role> [institution_id] [is_active]")
        print("If institution_id is omitted, a default institution will be created (if needed) and assigned.")
    else:
        username = sys.argv[1]
        full_name = sys.argv[2]
        email = sys.argv[3]
        phone = sys.argv[4]
        password = sys.argv[5]
        role = sys.argv[6]
        institution_id = int(sys.argv[7]) if len(sys.argv) > 7 else None
        is_active = sys.argv[8].lower() != 'false' if len(sys.argv) > 8 else True

        create_user(username, full_name, email, phone, password, role, institution_id, is_active)
