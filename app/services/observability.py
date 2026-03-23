from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class SourceMetric:
    success: int = 0
    failures: int = 0
    parse_errors: int = 0
    timeouts: int = 0
    rate_limited: int = 0
    unavailable: int = 0
    latencies_ms: list[int] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        total = self.success + self.failures
        return self.success / total if total else 0.0

    @property
    def p95_latency_ms(self) -> int:
        if not self.latencies_ms:
            return 0
        ordered = sorted(self.latencies_ms)
        idx = int((len(ordered) - 1) * 0.95)
        return ordered[idx]


class SourceMetricsRegistry:
    def __init__(self):
        self._metrics: dict[str, SourceMetric] = defaultdict(SourceMetric)

    def record_success(self, source_id: str, latency_ms: int) -> None:
        metric = self._metrics[source_id]
        metric.success += 1
        metric.latencies_ms.append(latency_ms)

    def record_failure(self, source_id: str, code: str) -> None:
        metric = self._metrics[source_id]
        metric.failures += 1
        if code == "parse_error":
            metric.parse_errors += 1
        elif code == "timeout":
            metric.timeouts += 1
        elif code == "rate_limited":
            metric.rate_limited += 1
        elif code == "unavailable":
            metric.unavailable += 1

    def snapshot(self, source_id: str) -> dict[str, float | int]:
        metric = self._metrics[source_id]
        return {
            "success": metric.success,
            "failures": metric.failures,
            "parse_errors": metric.parse_errors,
            "timeouts": metric.timeouts,
            "rate_limited": metric.rate_limited,
            "unavailable": metric.unavailable,
            "success_rate": round(metric.success_rate, 4),
            "p95_latency_ms": metric.p95_latency_ms,
        }

    def export_prometheus(self) -> str:
        lines: list[str] = []
        for source_id, metric in sorted(self._metrics.items()):
            labels = f'source="{source_id}"'
            lines.extend([
                f"star_source_success_total{{{labels}}} {metric.success}",
                f"star_source_failures_total{{{labels}}} {metric.failures}",
                f"star_source_parse_errors_total{{{labels}}} {metric.parse_errors}",
                f"star_source_timeouts_total{{{labels}}} {metric.timeouts}",
                f"star_source_rate_limited_total{{{labels}}} {metric.rate_limited}",
                f"star_source_unavailable_total{{{labels}}} {metric.unavailable}",
                f"star_source_success_rate{{{labels}}} {metric.success_rate:.6f}",
                f"star_source_p95_latency_ms{{{labels}}} {metric.p95_latency_ms}",
            ])
        return "\n".join(lines) + ("\n" if lines else "")


source_metrics = SourceMetricsRegistry()
