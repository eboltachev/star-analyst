import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("fastapi")

from app.models.models import Job, JobStatus, Request
from app.worker.run import claim_next_job


def test_claim_next_job_two_sessions_no_duplicate(client):
    SessionLocal = client.app.state.test_sessionmaker
    # seed 2 requests + jobs
    with SessionLocal() as db:
        r1 = Request(user_id=1, full_name="A", selected_sources=[])
        r2 = Request(user_id=1, full_name="B", selected_sources=[])
        db.add_all([r1, r2])
        db.commit()
        db.refresh(r1)
        db.refresh(r2)
        db.add_all([
            Job(request_id=r1.id, status=JobStatus.queued),
            Job(request_id=r2.id, status=JobStatus.queued),
        ])
        db.commit()

    with SessionLocal() as db1, SessionLocal() as db2:
        j1 = claim_next_job(db1)
        j2 = claim_next_job(db2)

    assert j1 is not None and j2 is not None
    assert j1.id != j2.id
