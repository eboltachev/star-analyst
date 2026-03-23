import json
from pathlib import Path

from app.services.adapters.base import AdapterError, BaseSourceAdapter, EvidenceRecord


class MvdWantedAdapter(BaseSourceAdapter):
    def _normalize(self, item: dict, query: dict) -> EvidenceRecord:
        self._require_item_fields(item, self._contract_required_fields())
        return EvidenceRecord(
            source_id=self.source_config["id"],
            title=str(item["title"]),
            raw_fragment=str(item["raw"]),
            normalized_fragment=str(item["normalized"]),
            url=item.get("url"),
            confidence=float(item.get("confidence", 0.7)),
            meta={"matched_by": query.get("full_name"), "runtime_mode": self.source_config.get("mode", "fixture")},
        )

    def search(self, query: dict) -> list[EvidenceRecord]:
        if self.source_config.get("mode") == "http":
            data = self._fetch_runtime_items(query)
        else:
            fixture = Path("tests/fixtures/mvd_wanted.json")
            data = json.loads(fixture.read_text(encoding="utf-8"))
        out: list[EvidenceRecord] = []
        for item in data:
            try:
                out.append(self._normalize(item, query))
            except (TypeError, ValueError) as exc:
                raise AdapterError("parse_error", f"{self.source_id}: invalid item shape") from exc
        return out
