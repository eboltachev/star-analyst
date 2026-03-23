from __future__ import annotations

from datetime import date, datetime
from enum import Enum

try:
    from enum import StrEnum
except ImportError:  # Python < 3.11
    class StrEnum(str, Enum):
        pass
from typing import Any
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Role(StrEnum):
    user = "user"
    admin = "admin"


class RequestStatus(StrEnum):
    created = "created"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.user)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    requests: Mapped[list[Request]] = relationship(back_populates="user")


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    inn: Mapped[str | None] = mapped_column(String(32), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    selected_sources: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus), default=RequestStatus.created)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="requests")
    files: Mapped[list[UploadedFile]] = relationship(back_populates="request", cascade="all, delete-orphan")
    source_runs: Mapped[list[SourceRun]] = relationship(back_populates="request", cascade="all, delete-orphan")
    evidence_items: Mapped[list[EvidenceItem]] = relationship(back_populates="request", cascade="all, delete-orphan")
    entities: Mapped[list[Entity]] = relationship(back_populates="request", cascade="all, delete-orphan")
    relations: Mapped[list[Relation]] = relationship(back_populates="request", cascade="all, delete-orphan")
    reports: Mapped[list[Report]] = relationship(back_populates="request", cascade="all, delete-orphan")
    events: Mapped[list[PipelineEvent]] = relationship(back_populates="request", cascade="all, delete-orphan")
    jobs: Mapped[list[Job]] = relationship(back_populates="request", cascade="all, delete-orphan")
    reruns: Mapped[list[RerunRun]] = relationship(back_populates="request", cascade="all, delete-orphan")


class JobStatus(StrEnum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), index=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.queued, index=True)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    request: Mapped[Request] = relationship(back_populates="jobs")


class RerunRun(Base):
    __tablename__ = "rerun_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), index=True)
    source_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    request: Mapped[Request] = relationship(back_populates="reruns")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(128))
    path: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    request: Mapped[Request] = relationship(back_populates="files")


class ExtractedArtifact(Base):
    __tablename__ = "extracted_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), index=True)
    uploaded_file_id: Mapped[int | None] = mapped_column(ForeignKey("uploaded_files.id"), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text)
    entities_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SourceConfig(Base):
    __tablename__ = "source_configs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    adapter: Mapped[str] = mapped_column(String(255))
    base_url: Mapped[str] = mapped_column(String(500))
    timeout: Mapped[int] = mapped_column(Integer, default=15)
    rate_limit: Mapped[float] = mapped_column(Float, default=1.0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class SourceRun(Base):
    __tablename__ = "source_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    request: Mapped[Request] = relationship(back_populates="source_runs")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_fragment: Mapped[str] = mapped_column(Text)
    normalized_fragment: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    acquired_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    meta_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    request: Mapped[Request] = relationship(back_populates="evidence_items")


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), index=True)
    type: Mapped[str] = mapped_column(String(64))
    value: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_item_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768).with_variant(JSON, "sqlite"), nullable=True)

    request: Mapped[Request] = relationship(back_populates="entities")


class Relation(Base):
    __tablename__ = "relations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), index=True)
    from_entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"))
    to_entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"))
    type: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text)
    evidence_item_ids: Mapped[list[int]] = mapped_column(JSON, default=list)

    request: Mapped[Request] = relationship(back_populates="relations")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), index=True)
    markdown: Mapped[str] = mapped_column(Text)
    claims_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    request: Mapped[Request] = relationship(back_populates="reports")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PipelineEvent(Base):
    __tablename__ = "pipeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), index=True)
    step: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32))
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    request: Mapped[Request] = relationship(back_populates="events")
