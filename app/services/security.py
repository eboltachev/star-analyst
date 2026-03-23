from __future__ import annotations

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
PDF_MAGIC = b"%PDF"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def detect_content_type(body: bytes) -> str:
    if body.startswith(PNG_MAGIC):
        return "image/png"
    if body.startswith(JPEG_MAGIC):
        return "image/jpeg"
    if body.startswith(PDF_MAGIC):
        return "application/pdf"
    # treat utf-8 / plain bytes as text fallback for MVP
    try:
        body.decode("utf-8")
        return "text/plain"
    except UnicodeDecodeError:
        return "application/octet-stream"


def validate_upload_content(declared_content_type: str | None, body: bytes, allowed_types: set[str]) -> tuple[bool, str]:
    detected = detect_content_type(body)
    declared = declared_content_type or "application/octet-stream"
    if declared not in allowed_types:
        return False, f"Unsupported declared file type: {declared}"
    if detected not in allowed_types:
        return False, f"Detected file type is not allowed: {detected}"
    # mismatch means spoofing
    if declared != detected and not ({declared, detected} <= {"text/plain", "application/octet-stream"}):
        return False, f"Declared type {declared} does not match detected type {detected}"
    return True, detected
