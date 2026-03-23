from app.services.ai import LLMProvider
from app.services.graph import build_graph_payload


class E:
    def __init__(self, i):
        self.id = i
        self.value = f"E{i}"
        self.type = "mention"
        self.description = "d"
        self.evidence_item_ids = [1]


class R:
    id = 1
    from_entity_id = 1
    to_entity_id = 2
    type = "related"
    description = "d"
    evidence_item_ids = [1]


def test_graph_building():
    graph = build_graph_payload([E(1), E(2)], [R()])
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1


def test_chat_no_hallucination_when_no_context():
    answer = LLMProvider().chat("Что найдено?", [])
    assert "Недостаточно данных" in answer
