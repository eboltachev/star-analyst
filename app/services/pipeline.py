from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import (
    Entity,
    EvidenceItem,
    ExtractedArtifact,
    PipelineEvent,
    Relation,
    Report,
    Request,
    RequestStatus,
    SourceRun,
)
from app.services.adapters import ADAPTERS
from app.services.adapters.base import AdapterError
from app.services.ai import EmbeddingProvider, LLMProvider, VisionProvider
from app.schemas.contracts import ReportClaim, ReportClaimsPayload
from app.services.observability import source_metrics
from app.services.quality import enforce_claim_coverage


STEPS = [
    "created request",
    "extract attachments",
    "search sources",
    "normalize results",
    "extract entities & relations",
    "build report",
    "build graph",
    "done",
]


def build_report_claims(evidences: list[EvidenceItem]) -> ReportClaimsPayload:
    claims = [
        ReportClaim(
            claim_id=f"claim-{ev.id}",
            text=ev.title,
            evidence_ids=[ev.id],
            confidence=ev.confidence,
            source_refs=[ev.source_id],
        )
        for ev in evidences
    ]
    return ReportClaimsPayload(claims=claims)


def emit(db: Session, request_id: str, step: str, status: str, message: str | None = None) -> None:
    db.add(PipelineEvent(request_id=request_id, step=step, status=status, message=message))
    db.commit()


def process_request(db: Session, request_id: str, sources: list[dict]) -> None:
    req = db.get(Request, request_id)
    if not req:
        return
    req.status = RequestStatus.processing
    db.commit()

    vision, llm, embed = VisionProvider(), LLMProvider(), EmbeddingProvider()
    emit(db, request_id, STEPS[0], "ok")

    emit(db, request_id, STEPS[1], "running")
    for f in req.files:
        ocr = vision.extract(f.path)
        db.add(ExtractedArtifact(request_id=request_id, uploaded_file_id=f.id, raw_text=ocr.text, entities_json=ocr.entities))
    emit(db, request_id, STEPS[1], "ok")

    emit(db, request_id, STEPS[2], "running")
    query = {"full_name": req.full_name, "inn": req.inn, "birth_date": str(req.birth_date) if req.birth_date else None}
    source_failures = 0
    for src in sources:
        if src["id"] not in req.selected_sources:
            continue
        run = SourceRun(request_id=request_id, source_id=src["id"], status="running", started_at=datetime.utcnow())
        db.add(run)
        db.commit()
        adapter = ADAPTERS[src["adapter"]](src)
        started = time.monotonic()
        try:
            records = adapter.search(query)
            for rec in records:
                db.add(EvidenceItem(
                    request_id=request_id,
                    source_id=rec.source_id,
                    title=rec.title,
                    url=rec.url,
                    raw_fragment=rec.raw_fragment,
                    normalized_fragment=rec.normalized_fragment,
                    confidence=rec.confidence,
                    meta_json=rec.meta or {},
                ))
            elapsed_ms = int((time.monotonic() - started) * 1000)
            source_metrics.record_success(src["id"], elapsed_ms)
            run.status = "ok"
            metrics = source_metrics.snapshot(src["id"])
            run.message = f"ok records={len(records)} latency_ms={elapsed_ms} success_rate={metrics['success_rate']} p95_latency_ms={metrics['p95_latency_ms']}"
            run.finished_at = datetime.utcnow()
            emit(db, request_id, f"source:{src['id']}", "ok", run.message)
        except AdapterError as exc:
            source_failures += 1
            source_metrics.record_failure(src["id"], exc.code)
            metrics = source_metrics.snapshot(src["id"])
            run.status = "error"
            run.message = f"code={exc.code}; retryable={exc.retryable}; message={exc}; success_rate={metrics['success_rate']}"
            run.finished_at = datetime.utcnow()
            emit(db, request_id, f"source:{src['id']}", "error", run.message)
        except Exception as exc:  # noqa: BLE001
            source_failures += 1
            source_metrics.record_failure(src["id"], "unknown")
            run.status = "error"
            run.message = f"code=unknown; retryable=false; message={exc}"
            run.finished_at = datetime.utcnow()
            emit(db, request_id, f"source:{src['id']}", "error", run.message)
        db.commit()
    emit(db, request_id, STEPS[2], "ok" if source_failures == 0 else "degraded", f"source_failures={source_failures}")

    emit(db, request_id, STEPS[4], "running")
    evidences = db.scalars(select(EvidenceItem).where(EvidenceItem.request_id == request_id)).all()
    entity_map: dict[str, Entity] = {}
    for ev in evidences:
        key = ev.title.split()[0]
        if key not in entity_map:
            ent = Entity(request_id=request_id, type="mention", value=key, description=ev.title, evidence_item_ids=[ev.id], embedding=embed.embed(ev.normalized_fragment))
            db.add(ent)
            db.flush()
            entity_map[key] = ent
        else:
            entity_map[key].evidence_item_ids.append(ev.id)
    vals = list(entity_map.values())
    if len(vals) > 1:
        for i in range(len(vals) - 1):
            db.add(Relation(request_id=request_id, from_entity_id=vals[i].id, to_entity_id=vals[i + 1].id, type="related", description="Shared request context", evidence_item_ids=vals[i].evidence_item_ids[:1]))
    db.commit()
    emit(db, request_id, STEPS[4], "ok")

    emit(db, request_id, STEPS[5], "running")
    report = llm.build_report({
        "request": {"full_name": req.full_name, "inn": req.inn, "birth_date": str(req.birth_date) if req.birth_date else None},
        "evidence": [{"id": e.id, "title": e.title} for e in evidences],
    })
    claims_payload = build_report_claims(evidences)
    if not enforce_claim_coverage(claims_payload, threshold=0.95):
        emit(db, request_id, STEPS[5], "error", "Claim coverage below threshold")
        req.status = RequestStatus.failed
        db.commit()
        return
    report_with_claims = report + "\n## Claims (report_claims_v1)\n" + "\n".join([f"- {c.claim_id}: {c.text} | evidence={c.evidence_ids}" for c in claims_payload.claims])
    db.add(Report(request_id=request_id, markdown=report_with_claims, claims_json=claims_payload.model_dump()))
    db.commit()
    emit(db, request_id, STEPS[5], "ok")
    emit(db, request_id, STEPS[6], "ok")
    emit(db, request_id, STEPS[7], "ok")
    req.status = RequestStatus.completed
    db.commit()


def save_upload(storage_path: Path, request_id: str, filename: str, body: bytes) -> str:
    target_dir = storage_path / request_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename
    target.write_bytes(body)
    return str(target)
