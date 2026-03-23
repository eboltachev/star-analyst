from __future__ import annotations

from io import BytesIO
import re
from pathlib import Path

import pytest

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


def _extract_csrf(html: str) -> str:
    m = re.search(r'name="csrf_token"\s+value="([a-f0-9]+)"', html)
    assert m
    return m.group(1)


@pytest.fixture()
def production_client(tmp_path: Path):
    old_testing = settings.testing
    old_csrf = settings.csrf_enabled
    settings.testing = False
    settings.csrf_enabled = True

    db_file = tmp_path / "prod_like.db"
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

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    settings.testing = old_testing
    settings.csrf_enabled = old_csrf


def test_login_requires_csrf_in_production_mode(production_client: TestClient):
    resp = production_client.post("/login", data={"email": "admin@example.com", "password": "admin123"}, follow_redirects=False)
    assert resp.status_code == 403


def test_upload_matrix_rejects_spoofed_content_type(production_client: TestClient):
    login_page = production_client.get("/login")
    csrf_login = _extract_csrf(login_page.text)
    login = production_client.post(
        "/login",
        data={"email": "admin@example.com", "password": "admin123", "csrf_token": csrf_login},
        follow_redirects=False,
    )
    assert login.status_code == 302

    home = production_client.get("/")
    csrf_request = _extract_csrf(home.text)

    fake_png = b"\x89PNG\r\n\x1a\n" + b"payload"
    files = [("files", ("malicious.txt", BytesIO(fake_png), "text/plain"))]
    resp = production_client.post(
        "/requests",
        data={"full_name": "Иванов Иван", "selected_sources": ["fns_registry"], "csrf_token": csrf_request},
        files=files,
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert "does not match" in resp.text
