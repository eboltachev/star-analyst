from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ReportClaim(BaseModel):
    claim_id: str
    text: str
    evidence_ids: list[int] = Field(default_factory=list)
    confidence: float | None = None
    source_refs: list[str] = Field(default_factory=list)

    @field_validator("evidence_ids")
    @classmethod
    def validate_evidence_ids(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("evidence_ids must not be empty")
        return v


class ReportClaimsPayload(BaseModel):
    version: str = "report_claims_v1"
    claims: list[ReportClaim] = Field(default_factory=list)


class ChatCitation(BaseModel):
    evidence_id: int
    source_id: str
    title: str
    url: str | None = None


class ChatAnswerPayload(BaseModel):
    version: str = "chat_answer_v1"
    answer: str
    citations: list[ChatCitation] = Field(default_factory=list)
    insufficient_data: bool = False
    suggested_reruns: list[str] = Field(default_factory=list)
