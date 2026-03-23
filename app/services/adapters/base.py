from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import json
import re
import time

import httpx

from app.services.adapters.contracts import get_contract


class AdapterError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.details = details or {}


@dataclass
class EvidenceRecord:
    source_id: str
    title: str
    raw_fragment: str
    normalized_fragment: str
    url: str | None = None
    confidence: float | None = None
    meta: dict[str, Any] | None = None


class BaseSourceAdapter:
    def __init__(self, source_config: dict):
        self.source_config = source_config
        self._last_request_at = 0.0

    def search(self, query: dict) -> list[EvidenceRecord]:
        raise NotImplementedError

    @property
    def source_id(self) -> str:
        return str(self.source_config.get("id", "unknown"))

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=self.source_config.get("timeout", 15))

    def _respect_rate_limit(self) -> None:
        rps = float(self.source_config.get("rate_limit", 1.0) or 1.0)
        min_interval = 1.0 / rps if rps > 0 else 0.0
        now = time.monotonic()
        delta = now - self._last_request_at
        if delta < min_interval:
            time.sleep(min_interval - delta)
        self._last_request_at = time.monotonic()

    def _get(self, url: str, params: dict[str, Any], retries: int = 2) -> httpx.Response:
        self._respect_rate_limit()
        attempt = 0
        while True:
            try:
                with self._client() as client:
                    resp = client.get(url, params=params)
                if resp.status_code == 429:
                    raise AdapterError("rate_limited", f"{self.source_id}: rate limited", retryable=True)
                if resp.status_code >= 500:
                    raise AdapterError("unavailable", f"{self.source_id}: upstream unavailable", retryable=True)
                if resp.status_code >= 400:
                    raise AdapterError("manual_required", f"{self.source_id}: upstream rejected request ({resp.status_code})")
                return resp
            except httpx.TimeoutException as exc:
                if attempt >= retries:
                    raise AdapterError("timeout", f"{self.source_id}: request timeout", retryable=True) from exc
            except httpx.HTTPError as exc:
                if attempt >= retries:
                    raise AdapterError("unavailable", f"{self.source_id}: connection error", retryable=True) from exc
            attempt += 1
            time.sleep(0.2 * attempt)


    def _contract_required_fields(self) -> tuple[str, ...]:
        contract = get_contract(self.source_id)
        if contract:
            return contract.required_fields
        return ("title", "raw", "normalized")

    def _validate_html_contract(self, body: str) -> None:
        contract = get_contract(self.source_id)
        if not contract or not contract.html_markers:
            return
        if not any(marker in body for marker in contract.html_markers):
            raise AdapterError("parse_error", f"{self.source_id}: parser contract drift detected")

    def _search_url_and_params(self, query: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        base_url = str(self.source_config["base_url"]).rstrip("/")
        search_path = str(self.source_config.get("search_path", "")).strip()
        url = f"{base_url}/{search_path.lstrip('/')}" if search_path else base_url
        param_map = self.source_config.get("query_param_map") or {}
        if not param_map:
            return url, query
        params: dict[str, Any] = {}
        for qkey, pkey in param_map.items():
            val = query.get(qkey)
            if val not in (None, ""):
                params[str(pkey)] = val
        return url, params

    def _extract_items(self, response: httpx.Response) -> list[dict[str, Any]]:
        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            try:
                payload = response.json()
            except Exception as exc:  # noqa: BLE001
                raise AdapterError("parse_error", f"{self.source_id}: invalid json payload") from exc
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                for key in ("items", "results", "data"):
                    value = payload.get(key)
                    if isinstance(value, list):
                        return value
            raise AdapterError("parse_error", f"{self.source_id}: unsupported json shape")

        body = response.text
        self._validate_html_contract(body)
        script_match = re.search(r"<script[^>]*application/json[^>]*>(.*?)</script>", body, flags=re.S | re.I)
        if script_match:
            try:
                payload = json.loads(script_match.group(1).strip())
            except json.JSONDecodeError as exc:
                raise AdapterError("parse_error", f"{self.source_id}: embedded json parse failed") from exc
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                for key in ("items", "results", "data"):
                    value = payload.get(key)
                    if isinstance(value, list):
                        return value

        rows = re.findall(
            r'<div[^>]*class=["\']evidence["\'][^>]*data-title=["\']([^"\']+)["\'][^>]*data-raw=["\']([^"\']+)["\'][^>]*data-normalized=["\']([^"\']+)["\'][^>]*>',
            body,
            flags=re.I,
        )
        if rows:
            return [{"title": t, "raw": r, "normalized": n} for t, r, n in rows]
        raise AdapterError("parse_error", f"{self.source_id}: unsupported html payload")

    def _fetch_runtime_items(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        url, params = self._search_url_and_params(query)
        response = self._get(url, params=params)
        return self._extract_items(response)

    def _require_item_fields(self, item: dict[str, Any], fields: tuple[str, ...]) -> None:
        missing = [field for field in fields if not item.get(field)]
        if missing:
            raise AdapterError(
                "parse_error",
                f"{self.source_id}: missing required fields: {', '.join(missing)}",
                details={"missing": missing},
            )
