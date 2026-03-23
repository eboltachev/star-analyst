from pathlib import Path

import pytest


@pytest.fixture()
def client(tmp_path: Path):
    pytest.importorskip("fastapi")
    pytest.importorskip("sqlalchemy")

    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings
    from app.db.base import Base
    from app.db.session import get_db
    from app.main import app
    from app.models.models import User
    from app.services.security import hash_password

    settings.testing = True
    db_file = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestingSessionLocal() as db:
        db.add(User(email="admin@example.com", password_hash=hash_password("admin123"), role="admin"))
        db.commit()
    app.state.test_sessionmaker = TestingSessionLocal
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    settings.testing = False
