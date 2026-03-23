import pytest

pytest.importorskip("httpx")

from app.services.adapters.fns import FnsRegistryAdapter


def test_fns_normalization():
    adapter = FnsRegistryAdapter({"id": "fns_registry", "timeout": 10})
    out = adapter.search({"inn": "123456789012"})
    assert out
    assert out[0].source_id == "fns_registry"
    assert "Ромашка" in out[0].normalized_fragment
