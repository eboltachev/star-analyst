from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Entity, Relation


def build_graph_payload(entities: list["Entity"], relations: list["Relation"]) -> dict:
    nodes = [
        {"data": {"id": str(e.id), "label": e.value, "type": e.type, "description": e.description or "", "evidence": e.evidence_item_ids}}
        for e in entities
    ]
    edges = [
        {"data": {"id": f"r-{r.id}", "source": str(r.from_entity_id), "target": str(r.to_entity_id), "type": r.type, "description": r.description, "evidence": r.evidence_item_ids}}
        for r in relations
    ]
    return {"nodes": nodes, "edges": edges}
