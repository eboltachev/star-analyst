import pytest

pytest.importorskip("pydantic")

from app.schemas.contracts import ChatAnswerPayload, ChatCitation, ReportClaim, ReportClaimsPayload


def test_report_claims_payload_v1():
    payload = ReportClaimsPayload(claims=[ReportClaim(claim_id="c1", text="fact", evidence_ids=[1], source_refs=["fns_registry"])])
    assert payload.version == "report_claims_v1"
    assert payload.claims[0].evidence_ids == [1]


def test_chat_answer_payload_v1():
    payload = ChatAnswerPayload(answer="ok", citations=[ChatCitation(evidence_id=1, source_id="sudrf", title="t")])
    assert payload.version == "chat_answer_v1"
    assert payload.insufficient_data is False


def test_report_claim_requires_evidence():
    with pytest.raises(Exception):
        ReportClaim(claim_id="c2", text="bad", evidence_ids=[])
