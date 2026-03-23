"""initial

Revision ID: 0001_initial
Revises: None
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table("users", sa.Column("id", sa.Integer, primary_key=True), sa.Column("email", sa.String(255), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("role", sa.String(16), nullable=False), sa.Column("created_at", sa.DateTime, nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("requests", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False), sa.Column("full_name", sa.String(255), nullable=False), sa.Column("birth_date", sa.Date, nullable=True), sa.Column("inn", sa.String(32)), sa.Column("comment", sa.Text), sa.Column("selected_sources", sa.JSON), sa.Column("status", sa.String(32), nullable=False), sa.Column("created_at", sa.DateTime), sa.Column("updated_at", sa.DateTime))
    op.create_table("jobs", sa.Column("id", sa.Integer, primary_key=True), sa.Column("request_id", sa.String(36), sa.ForeignKey("requests.id"), index=True), sa.Column("status", sa.String(32), index=True), sa.Column("attempt", sa.Integer, default=0), sa.Column("max_attempts", sa.Integer, default=3), sa.Column("error", sa.Text), sa.Column("locked_at", sa.DateTime), sa.Column("locked_by", sa.String(128)), sa.Column("created_at", sa.DateTime), sa.Column("updated_at", sa.DateTime))
    op.create_table("uploaded_files", sa.Column("id", sa.Integer, primary_key=True), sa.Column("request_id", sa.String(36), sa.ForeignKey("requests.id")), sa.Column("filename", sa.String(255)), sa.Column("content_type", sa.String(128)), sa.Column("path", sa.String(500)), sa.Column("created_at", sa.DateTime))
    op.create_table("extracted_artifacts", sa.Column("id", sa.Integer, primary_key=True), sa.Column("request_id", sa.String(36), sa.ForeignKey("requests.id")), sa.Column("uploaded_file_id", sa.Integer, sa.ForeignKey("uploaded_files.id"), nullable=True), sa.Column("raw_text", sa.Text), sa.Column("entities_json", sa.JSON), sa.Column("created_at", sa.DateTime))
    op.create_table("source_configs", sa.Column("id", sa.String(64), primary_key=True), sa.Column("name", sa.String(255)), sa.Column("enabled", sa.Boolean), sa.Column("adapter", sa.String(255)), sa.Column("base_url", sa.String(500)), sa.Column("timeout", sa.Integer), sa.Column("rate_limit", sa.Float), sa.Column("description", sa.Text))
    op.create_table("source_runs", sa.Column("id", sa.Integer, primary_key=True), sa.Column("request_id", sa.String(36), sa.ForeignKey("requests.id")), sa.Column("source_id", sa.String(64)), sa.Column("status", sa.String(32)), sa.Column("message", sa.Text), sa.Column("started_at", sa.DateTime), sa.Column("finished_at", sa.DateTime))
    op.create_table("evidence_items", sa.Column("id", sa.Integer, primary_key=True), sa.Column("request_id", sa.String(36), sa.ForeignKey("requests.id")), sa.Column("source_id", sa.String(64)), sa.Column("title", sa.String(255)), sa.Column("url", sa.String(500)), sa.Column("raw_fragment", sa.Text), sa.Column("normalized_fragment", sa.Text), sa.Column("confidence", sa.Float), sa.Column("acquired_at", sa.DateTime), sa.Column("meta_json", sa.JSON))
    op.create_table("entities", sa.Column("id", sa.Integer, primary_key=True), sa.Column("request_id", sa.String(36), sa.ForeignKey("requests.id")), sa.Column("type", sa.String(64)), sa.Column("value", sa.String(255)), sa.Column("description", sa.Text), sa.Column("evidence_item_ids", sa.JSON), sa.Column("embedding", Vector(768)))
    op.create_table("relations", sa.Column("id", sa.Integer, primary_key=True), sa.Column("request_id", sa.String(36), sa.ForeignKey("requests.id")), sa.Column("from_entity_id", sa.Integer, sa.ForeignKey("entities.id")), sa.Column("to_entity_id", sa.Integer, sa.ForeignKey("entities.id")), sa.Column("type", sa.String(64)), sa.Column("description", sa.Text), sa.Column("evidence_item_ids", sa.JSON))
    op.create_table("reports", sa.Column("id", sa.Integer, primary_key=True), sa.Column("request_id", sa.String(36), sa.ForeignKey("requests.id")), sa.Column("markdown", sa.Text), sa.Column("created_at", sa.DateTime))
    op.create_table("chat_sessions", sa.Column("id", sa.Integer, primary_key=True), sa.Column("request_id", sa.String(36), sa.ForeignKey("requests.id")), sa.Column("created_at", sa.DateTime))
    op.create_table("chat_messages", sa.Column("id", sa.Integer, primary_key=True), sa.Column("session_id", sa.Integer, sa.ForeignKey("chat_sessions.id")), sa.Column("role", sa.String(32)), sa.Column("message", sa.Text), sa.Column("created_at", sa.DateTime))
    op.create_table("pipeline_events", sa.Column("id", sa.Integer, primary_key=True), sa.Column("request_id", sa.String(36), sa.ForeignKey("requests.id")), sa.Column("step", sa.String(128)), sa.Column("status", sa.String(32)), sa.Column("message", sa.Text), sa.Column("created_at", sa.DateTime))


def downgrade() -> None:
    for t in ["pipeline_events", "chat_messages", "jobs", "chat_sessions", "reports", "relations", "entities", "evidence_items", "source_runs", "source_configs", "extracted_artifacts", "uploaded_files", "requests", "users"]:
        op.drop_table(t)
