from app.services.observability import SourceMetricsRegistry


def test_source_metrics_snapshot():
    registry = SourceMetricsRegistry()
    registry.record_success("fns_registry", 100)
    registry.record_success("fns_registry", 200)
    registry.record_failure("fns_registry", "parse_error")

    snap = registry.snapshot("fns_registry")
    assert snap["success"] == 2
    assert snap["failures"] == 1
    assert snap["parse_errors"] == 1
    assert snap["success_rate"] == 0.6667
    assert snap["p95_latency_ms"] == 100
