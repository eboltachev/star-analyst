from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

pytest.importorskip("httpx")

from app.services.adapters.base import AdapterError
from app.services.adapters.fns import FnsRegistryAdapter
from app.services.adapters.mvd import MvdWantedAdapter


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path == "/fns":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            payload = {
                "items": [
                    {
                        "title": "ООО Тест",
                        "raw": "raw",
                        "normalized": f"match={qs.get('q', [''])[0]}",
                    }
                ]
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        if parsed.path == "/mvd":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b'<div class="evidence" data-title="Card" data-raw="raw html" data-normalized="normalized html"></div>'
            )
            return

        if parsed.path == "/rate-limited":
            self.send_response(429)
            self.end_headers()
            return

        if parsed.path == "/drift":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<html><body><p>layout changed</p></body></html>")
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):  # noqa: A003
        return


@pytest.fixture()
def mock_server():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


def test_runtime_http_json_profile(mock_server):
    adapter = FnsRegistryAdapter(
        {
            "id": "fns_registry",
            "mode": "http",
            "base_url": mock_server,
            "search_path": "/fns",
            "query_param_map": {"inn": "q"},
            "timeout": 2,
            "rate_limit": 5,
        }
    )
    rows = adapter.search({"inn": "123"})
    assert len(rows) == 1
    assert rows[0].normalized_fragment == "match=123"


def test_runtime_http_html_profile(mock_server):
    adapter = MvdWantedAdapter(
        {
            "id": "mvd_wanted",
            "mode": "http",
            "base_url": mock_server,
            "search_path": "/mvd",
            "timeout": 2,
        }
    )
    rows = adapter.search({"full_name": "Ivanov"})
    assert len(rows) == 1
    assert rows[0].title == "Card"


def test_runtime_error_taxonomy_rate_limit(mock_server):
    adapter = FnsRegistryAdapter(
        {
            "id": "fns_registry",
            "mode": "http",
            "base_url": mock_server,
            "search_path": "/rate-limited",
            "timeout": 1,
        }
    )
    with pytest.raises(AdapterError) as exc:
        adapter.search({"inn": "123"})
    assert exc.value.code == "rate_limited"


def test_runtime_contract_drift_detected(mock_server):
    adapter = MvdWantedAdapter(
        {
            "id": "mvd_wanted",
            "mode": "http",
            "base_url": mock_server,
            "search_path": "/drift",
            "timeout": 2,
        }
    )
    with pytest.raises(AdapterError) as exc:
        adapter.search({"full_name": "Ivanov"})
    assert exc.value.code == "parse_error"
