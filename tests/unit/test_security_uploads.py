import pytest

pytest.importorskip("passlib")

from app.services.security import validate_upload_content


def test_upload_rejects_mismatched_content_type():
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"abc"
    allowed = {"image/png", "text/plain", "application/pdf", "image/jpeg"}
    ok, message = validate_upload_content("text/plain", png_bytes, allowed)
    assert ok is False
    assert "does not match" in message


def test_upload_accepts_text_plain():
    body = "hello".encode("utf-8")
    allowed = {"image/png", "text/plain", "application/pdf", "image/jpeg"}
    ok, detected = validate_upload_content("text/plain", body, allowed)
    assert ok is True
    assert detected == "text/plain"
