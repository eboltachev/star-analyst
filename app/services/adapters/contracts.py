from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceParserContract:
    source_id: str
    required_fields: tuple[str, ...]
    html_markers: tuple[str, ...] = ()


CONTRACTS: dict[str, SourceParserContract] = {
    "fns_registry": SourceParserContract(
        source_id="fns_registry",
        required_fields=("title", "raw", "normalized"),
        html_markers=("evidence",),
    ),
    "sudrf": SourceParserContract(
        source_id="sudrf",
        required_fields=("title", "raw", "normalized"),
        html_markers=("evidence",),
    ),
    "mvd_wanted": SourceParserContract(
        source_id="mvd_wanted",
        required_fields=("title", "raw", "normalized"),
        html_markers=("evidence",),
    ),
}


def get_contract(source_id: str) -> SourceParserContract | None:
    return CONTRACTS.get(source_id)
