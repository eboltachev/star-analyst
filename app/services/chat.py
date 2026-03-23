from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import ChatMessage, ChatSession, EvidenceItem, Report
from app.services.ai import LLMProvider
from app.schemas.contracts import ChatAnswerPayload, ChatCitation
from app.services.quality import enforce_chat_policy


def ask_report_chat(db: Session, request_id: str, question: str) -> ChatAnswerPayload:
    session = db.scalar(select(ChatSession).where(ChatSession.request_id == request_id))
    if not session:
        session = ChatSession(request_id=request_id)
        db.add(session)
        db.flush()
    db.add(ChatMessage(session_id=session.id, role="user", message=question))

    report = db.scalar(select(Report).where(Report.request_id == request_id).order_by(Report.id.desc()))
    evidence = db.scalars(select(EvidenceItem).where(EvidenceItem.request_id == request_id)).all()
    citations = [ChatCitation(evidence_id=e.id, source_id=e.source_id, title=e.title, url=e.url) for e in evidence[:5]]
    chunks = [f"evidence:{e.id}:{e.title}" for e in evidence]
    if report:
        chunks.insert(0, report.markdown[:240])

    if not citations:
        answer_payload = ChatAnswerPayload(
            answer="Недостаточно данных для подтверждённого ответа.",
            citations=[],
            insufficient_data=True,
            suggested_reruns=["fns_registry", "sudrf", "mvd_wanted"],
        )
    else:
        answer_payload = ChatAnswerPayload(
            answer=LLMProvider().chat(question, chunks),
            citations=citations,
            insufficient_data=False,
            suggested_reruns=[],
        )

    if not enforce_chat_policy(answer_payload):
        answer_payload = ChatAnswerPayload(
            answer="Недостаточно данных для подтверждённого ответа.",
            citations=[],
            insufficient_data=True,
            suggested_reruns=["fns_registry", "sudrf", "mvd_wanted"],
        )

    db.add(ChatMessage(session_id=session.id, role="assistant", message=answer_payload.answer))
    db.commit()
    return answer_payload
