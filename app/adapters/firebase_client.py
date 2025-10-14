# app/adapters/firebase_client.py
import os
import json
import base64
import firebase_admin
from firebase_admin import credentials
from app.config import settings

_app = None  # lazy-inited firebase app

def _get_raw_cred_string() -> str:
    """
    Try common env/config sources. Order:
    1) FIREBASE_CREDENTIALS (raw JSON or base64)
    2) GOOGLE_APPLICATION_CREDENTIALS (path OR raw JSON OR base64)
    """
    return (
        os.getenv("FIREBASE_CREDENTIALS", "").strip()
        or os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
        or getattr(settings, "FIREBASE_CREDENTIALS", "")  # optional in your settings
        or getattr(settings, "GOOGLE_APPLICATION_CREDENTIALS", "")
    ).strip()

def _build_credentials() -> credentials.Certificate:
    raw = _get_raw_cred_string()
    if not raw:
        raise RuntimeError(
            "Firebase credentials not provided. Set FIREBASE_CREDENTIALS (JSON/base64) "
            "or GOOGLE_APPLICATION_CREDENTIALS (path/JSON/base64)."
        )

    # Case A: looks like a filesystem path
    if raw.endswith(".json") or raw.startswith(("/", "./", "../")):
        return credentials.Certificate(raw)

    # Case B: raw JSON pasted into the variable
    if raw[:1] in ("{", "["):
        data = json.loads(raw)  # raises JSONDecodeError if malformed
        return credentials.Certificate(data)

    # Case C: base64-encoded JSON (common for CI/CD)
    try:
        decoded = base64.b64decode(raw, validate=True).decode("utf-8")
        data = json.loads(decoded)
        return credentials.Certificate(data)
    except Exception as e:
        raise RuntimeError(
            "Could not parse Firebase credentials (not a path, JSON, or valid base64-JSON)."
        ) from e

def get_firebase_client():
    """
    Lazy initialize on first use so imports don't crash.
    """
    global _app
    if _app is None:
        cred = _build_credentials()
        try:
            _app = firebase_admin.get_app()
        except ValueError:
            _app = firebase_admin.initialize_app(cred)
    return _app
