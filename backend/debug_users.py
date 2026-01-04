from database import SessionLocal
import models
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def list_users():
    db = SessionLocal()
    users = db.query(models.User).all()
    print(f"Total Users: {len(users)}")
    for user in users:
        print(f"User: {user.email}, ID: {user.id}, Role: {user.role}, Name: {user.name}")
    db.close()

def create_user(email, password, role="member", name=None, phone=None):
    db = SessionLocal()
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        print(f"User {email} already exists. Updating details.")
        existing_user.role = role
        if name: existing_user.name = name
        if phone: existing_user.phone_number = phone
        existing_user.hashed_password = get_password_hash(password)
        db.commit()
    else:
        hashed_password = get_password_hash(password)
        user = models.User(email=email, hashed_password=hashed_password, role=role, name=name, phone_number=phone)
        db.add(user)
        db.commit()
        print(f"Created user {email} with role {role}")
    db.close()

if __name__ == "__main__":
    print("--- Listing Users ---")
    list_users()
    print("\n--- Creating/Updating Admin User ---")
    create_user("admin@adidas.com", "admin123", role="admin", name="Super Admin", phone="08123456789")
    print("\n--- Creating/Updating Member User ---")
    create_user("test@adidas.com", "password123", role="member", name="John Doe", phone="081298765432")
    print("\n--- Listing Users Again ---")
    list_users()
