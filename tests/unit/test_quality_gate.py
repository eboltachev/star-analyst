import pytest

pytest.importorskip("pydantic")

from app.schemas.contracts import ChatAnswerPayload, ReportClaim, ReportClaimsPayload
from app.services.quality import claim_coverage, enforce_chat_policy, enforce_claim_coverage


def test_claim_coverage_enforced():
    payload = ReportClaimsPayload(claims=[ReportClaim(claim_id="1", text="fact", evidence_ids=[1], source_refs=["fns"])])
    assert claim_coverage(payload) == 1.0
    assert enforce_claim_coverage(payload, 0.95)


def test_chat_policy_requires_citations_or_insufficient_data():
    invalid = ChatAnswerPayload(answer="x", citations=[], insufficient_data=False, suggested_reruns=[])
    assert enforce_chat_policy(invalid) is False

    valid_with_citation = ChatAnswerPayload(
        answer="x",
        citations=[{"evidence_id": 1, "source_id": "fns", "title": "t", "url": None}],
        insufficient_data=False,
        suggested_reruns=[],
    )
    assert enforce_chat_policy(valid_with_citation) is True

    valid_insufficient = ChatAnswerPayload(answer="x", citations=[], insufficient_data=True, suggested_reruns=["fns_registry"])
    assert enforce_chat_policy(valid_insufficient) is True
