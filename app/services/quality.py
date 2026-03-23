from app.schemas.contracts import ChatAnswerPayload, ReportClaimsPayload


def claim_coverage(payload: ReportClaimsPayload) -> float:
    if not payload.claims:
        return 0.0
    covered = sum(1 for c in payload.claims if c.evidence_ids)
    return covered / len(payload.claims)


def enforce_claim_coverage(payload: ReportClaimsPayload, threshold: float = 0.95) -> bool:
    return claim_coverage(payload) >= threshold


def enforce_chat_policy(payload: ChatAnswerPayload) -> bool:
    """Chat must provide citations or explicitly declare insufficiency."""
    has_citations = bool(payload.citations)
    return has_citations or payload.insufficient_data
