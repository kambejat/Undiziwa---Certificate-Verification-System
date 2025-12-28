import sys
from app import create_app, db
from models import Institution

app = create_app()
app.app_context().push()

def create_institution(name, email, phone):
    existing = Institution.query.filter_by(institution_name=name).first()
    if existing:
        print(f"Institution '{name}' already exists with ID {existing.institution_id}.")
        return existing

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

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_institution.py <name> <email> <phone>")
    else:
        _, name, email, phone = sys.argv
        create_institution(name, email, phone)
