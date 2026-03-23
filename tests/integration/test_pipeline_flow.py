from io import BytesIO

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("fastapi")

from app.worker.run import process_once


def login(client):
    return client.post("/login", data={"email": "admin@example.com", "password": "admin123"}, follow_redirects=True)


def test_create_request_enqueue_and_worker_report(client):
    login(client)
    files = [("files", ("sample.txt", BytesIO("Иванов Иван Иванович 123456789012".encode()), "text/plain"))]
    r = client.post("/requests", data={"full_name": "Иванов Иван Иванович", "birth_date": "1990-01-01", "inn": "123456789012", "selected_sources": ["fns_registry", "sudrf"]}, files=files, follow_redirects=False)
    assert r.status_code == 302
    monitor_url = r.headers["location"]
    req_id = monitor_url.split("/")[2]

    SessionLocal = client.app.state.test_sessionmaker
    with SessionLocal() as db:
        handled = process_once(db)
        assert handled is True

    rep = client.get(f"/requests/{req_id}/report")
    assert rep.status_code == 200
    assert "Аналитическая справка" in rep.text

    ch = client.post(f"/requests/{req_id}/chat", data={"question": "На чем основано?"})
    assert ch.status_code == 200
    body = ch.json()
    assert "answer" in body
    assert "citations" in body
    assert body["version"] == "chat_answer_v1"
    assert body["insufficient_data"] is False


def test_rerun_lifecycle_updates_status(client):
    login(client)
    files = [("files", ("sample.txt", BytesIO("Иванов Иван Иванович 123456789012".encode()), "text/plain"))]
    r = client.post("/requests", data={"full_name": "Иванов Иван Иванович", "birth_date": "1990-01-01", "inn": "123456789012", "selected_sources": ["fns_registry"]}, files=files, follow_redirects=False)
    req_id = r.headers["location"].split("/")[2]

    rr = client.post(f"/requests/{req_id}/rerun", data={"rerun_sources": ["fns_registry"]}, follow_redirects=False)
    assert rr.status_code == 302

    SessionLocal = client.app.state.test_sessionmaker
    with SessionLocal() as db:
        process_once(db)

    report = client.get(f"/requests/{req_id}/report")
    assert report.status_code == 200
    assert "История rerun" in report.text
    assert "done" in report.text


def test_metrics_endpoint_exports_source_metrics(client):
    login(client)
    files = [("files", ("sample.txt", BytesIO("Иванов Иван Иванович 123456789012".encode()), "text/plain"))]
    r = client.post(
        "/requests",
        data={"full_name": "Иванов Иван Иванович", "birth_date": "1990-01-01", "inn": "123456789012", "selected_sources": ["fns_registry"]},
        files=files,
        follow_redirects=False,
    )
    req_id = r.headers["location"].split("/")[2]

    SessionLocal = client.app.state.test_sessionmaker
    with SessionLocal() as db:
        process_once(db)

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "star_source_success_total" in metrics.text
    assert "fns_registry" in metrics.text
