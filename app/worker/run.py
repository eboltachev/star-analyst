import socket
import time
from datetime import datetime
from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.models import Job, JobStatus, Request, RerunRun
from app.services.pipeline import process_request
from app.services.sources import load_sources


def claim_next_job(db) -> Job | None:
    stmt = (
        select(Job)
        .where(Job.status == JobStatus.queued)
        .order_by(Job.created_at.asc())
        .limit(1)
    )
    if db.bind and db.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)
    job = db.scalar(stmt)
    if not job:
        return None
    job.status = JobStatus.running
    job.attempt += 1
    job.locked_at = datetime.utcnow()
    job.locked_by = socket.gethostname()
    db.commit()
    db.refresh(job)
    return job


def _claim_pending_rerun(db, request_id: str) -> RerunRun | None:
    stmt = (
        select(RerunRun)
        .where(RerunRun.request_id == request_id, RerunRun.status == "queued")
        .order_by(RerunRun.created_at.desc())
        .limit(1)
    )
    rerun = db.scalar(stmt)
    if not rerun:
        return None
    rerun.status = "running"
    db.commit()
    db.refresh(rerun)
    return rerun


def process_once(db) -> bool:
    job = claim_next_job(db)
    if not job:
        return False
    rerun_run: RerunRun | None = None
    try:
        req = db.get(Request, job.request_id)
        if not req:
            job.status = JobStatus.failed
            job.error = "Request not found"
            db.commit()
            return True

        rerun_run = _claim_pending_rerun(db, req.id)
        process_request(db, req.id, load_sources(settings.sources_config_path))

        if rerun_run:
            rerun_run.status = "done"
        job.status = JobStatus.done
        job.error = None
    except Exception as exc:  # noqa: BLE001
        if rerun_run:
            rerun_run.status = "error"
        if job.attempt >= job.max_attempts:
            job.status = JobStatus.failed
            job.error = str(exc)
        else:
            job.status = JobStatus.queued
            job.error = str(exc)
    db.commit()
    return True


def run() -> None:
    while True:
        with SessionLocal() as db:
            process_once(db)
        time.sleep(settings.worker_poll_interval_seconds)


if __name__ == "__main__":
    run()
