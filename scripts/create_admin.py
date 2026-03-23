from app.db.session import SessionLocal
from app.models.models import User
from app.services.security import hash_password

with SessionLocal() as db:
    if not db.query(User).filter_by(email="admin@example.com").first():
        db.add(User(email="admin@example.com", password_hash=hash_password("admin123"), role="admin"))
        db.commit()
        print("admin created")
    else:
        print("admin exists")
