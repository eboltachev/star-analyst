from __future__ import annotations

import asyncio
import json
import secrets
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine, get_db
from app.models.models import Job, JobStatus, PipelineEvent, Report, Request as CheckRequest, RerunRun, SourceRun, UploadedFile, User
from app.services.chat import ask_report_chat
from app.services.pipeline import save_upload
from app.services.security import hash_password, validate_upload_content, verify_password
from app.services.sources import load_sources
from app.services.graph import build_graph_payload
from app.services.observability import source_metrics
from app.models.models import Entity, Relation
from app.schemas.contracts import ChatAnswerPayload

configure_logging()
app = FastAPI(title=settings.app_name)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, session_cookie=settings.session_cookie_name, https_only=settings.session_cookie_secure, same_site=settings.session_same_site)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def get_csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_hex(16)
        request.session["csrf_token"] = token
    return token


def verify_csrf(request: Request, csrf_token: str) -> None:
    if not settings.csrf_enabled:
        return
    if settings.testing:
        return
    if not csrf_token or csrf_token != request.session.get("csrf_token"):
        raise HTTPException(status_code=403, detail="CSRF validation failed")


@app.on_event("startup")
def startup() -> None:
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    uid = request.session.get("uid")
    if not uid:
        return RedirectResponse("/login", status_code=302)
    sources = [s for s in load_sources(settings.sources_config_path) if s.get("enabled", True)]
    return templates.TemplateResponse("new_request.html", {"request": request, "sources": sources, "csrf_token": get_csrf_token(request)})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "csrf_token": get_csrf_token(request)})


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), csrf_token: str = Form(""), db: Session = Depends(get_db)):
    verify_csrf(request, csrf_token)
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    request.session["uid"] = user.id
    return RedirectResponse("/", status_code=302)


@app.post("/logout")
def logout(request: Request, csrf_token: str = Form("")):
    verify_csrf(request, csrf_token)
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


@app.post("/seed-admin")
def seed_admin(db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == "admin@example.com")):
        return {"ok": True}
    db.add(User(email="admin@example.com", password_hash=hash_password("admin123"), role="admin"))
    db.commit()
    return {"ok": True}


@app.post("/requests")
async def create_request(
    request: Request,
    full_name: str = Form(...),
    birth_date: str | None = Form(None),
    inn: str | None = Form(None),
    comment: str | None = Form(None),
    selected_sources: list[str] = Form(default=[]),
    files: list[UploadFile] = File(default=[]),
    csrf_token: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    verify_csrf(request, csrf_token)
    payload = CheckRequest(
        user_id=user.id,
        full_name=full_name,
        birth_date=datetime.strptime(birth_date, "%Y-%m-%d").date() if birth_date else None,
        inn=inn,
        comment=comment,
        selected_sources=selected_sources,
    )
    db.add(payload)
    db.commit()
    db.refresh(payload)
    allowed_types = {x.strip() for x in settings.upload_allowed_types.split(",") if x.strip()}
    max_size = settings.upload_max_size_mb * 1024 * 1024
    for upl in files:
        body = await upl.read()
        if len(body) > max_size:
            raise HTTPException(status_code=400, detail="File too large")
        valid, normalized_content_type = validate_upload_content(upl.content_type, body, allowed_types)
        if not valid:
            raise HTTPException(status_code=400, detail=normalized_content_type)
        path = save_upload(settings.storage_path, payload.id, upl.filename, body)
        db.add(UploadedFile(request_id=payload.id, filename=upl.filename, content_type=normalized_content_type, path=path))
    db.commit()

    db.add(Job(request_id=payload.id, status=JobStatus.queued))
    db.add(PipelineEvent(request_id=payload.id, step="created request", status="ok", message="Request enqueued"))
    db.commit()
    return RedirectResponse(f"/requests/{payload.id}/monitor", status_code=302)


@app.get("/requests/{request_id}/monitor", response_class=HTMLResponse)
def monitor_page(request_id: str, request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("monitor.html", {"request": request, "request_id": request_id, "user": user, "csrf_token": get_csrf_token(request)})


@app.get("/requests/{request_id}/events")
async def stream_events(request_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    async def event_generator():
        sent = 0
        while True:
            events = db.scalars(select(PipelineEvent).where(PipelineEvent.request_id == request_id).order_by(PipelineEvent.id)).all()
            if len(events) > sent:
                for ev in events[sent:]:
                    yield f"data: {json.dumps({'step': ev.step, 'status': ev.status, 'message': ev.message})}\n\n"
                sent = len(events)
            req = db.get(CheckRequest, request_id)
            if req and req.status in {"completed", "failed"}:
                break
            await asyncio.sleep(1)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/requests/{request_id}/report", response_class=HTMLResponse)
def report_page(request_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    req = db.get(CheckRequest, request_id)
    report = db.scalar(select(Report).where(Report.request_id == request_id).order_by(Report.id.desc()))
    entities = db.scalars(select(Entity).where(Entity.request_id == request_id)).all()
    relations = db.scalars(select(Relation).where(Relation.request_id == request_id)).all()
    graph = build_graph_payload(entities, relations)
    sources = [s for s in load_sources(settings.sources_config_path) if s.get("enabled", True)]
    source_runs = db.scalars(select(SourceRun).where(SourceRun.request_id == request_id).order_by(SourceRun.id.desc())).all()
    reruns = db.scalars(select(RerunRun).where(RerunRun.request_id == request_id).order_by(RerunRun.id.desc())).all()
    return templates.TemplateResponse("report.html", {"request": request, "item": req, "report": report, "graph": graph, "sources": sources, "source_runs": source_runs, "reruns": reruns, "csrf_token": get_csrf_token(request)})


@app.post("/requests/{request_id}/chat", response_model=ChatAnswerPayload)
def chat(request: Request, request_id: str, question: str = Form(...), csrf_token: str = Form(""), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    verify_csrf(request, csrf_token)
    return ask_report_chat(db, request_id, question)


@app.post("/requests/{request_id}/rerun")
def rerun_sources(request: Request, request_id: str, rerun_sources: list[str] = Form(default=[]), csrf_token: str = Form(""), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    verify_csrf(request, csrf_token)
    req = db.get(CheckRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    sources_to_run = rerun_sources or req.selected_sources
    db.add(RerunRun(request_id=req.id, source_ids=sources_to_run, status="queued"))
    db.add(Job(request_id=req.id, status=JobStatus.queued))
    db.add(PipelineEvent(request_id=req.id, step="rerun requested", status="ok", message="Sources rerun enqueued"))
    db.commit()
    return RedirectResponse(f"/requests/{request_id}/monitor", status_code=302)


@app.get("/history", response_class=HTMLResponse)
def history(request: Request, q: str = "", status: str = "", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(CheckRequest).where(CheckRequest.user_id == user.id)
    if q:
        stmt = stmt.where(or_(CheckRequest.full_name.ilike(f"%{q}%"), CheckRequest.inn.ilike(f"%{q}%")))
    if status:
        stmt = stmt.where(CheckRequest.status == status)
    items = db.scalars(stmt.order_by(CheckRequest.created_at.desc())).all()
    return templates.TemplateResponse("history.html", {"request": request, "items": items, "q": q, "status": status, "csrf_token": get_csrf_token(request)})


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(source_metrics.export_prometheus(), media_type="text/plain; version=0.0.4")
