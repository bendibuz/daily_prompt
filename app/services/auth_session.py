# auth_session.py
from datetime import datetime, timezone, timedelta
from firebase_admin import firestore
from app.adapters.firebase_client import get_firebase_client

get_firebase_client()
database = firestore.client()

def now_utc(): 
    return datetime.now(timezone.utc)

def get_auth_session(e164: str) -> dict | None:
    doc = database.collection("auth_sessions").document(e164).get()
    return doc.to_dict() if doc.exists else None

def set_auth_session(e164: str, phase: str, expires_in_minutes: int = 10, attempts: int = 0):
    database.collection("auth_sessions").document(e164).set({
        "phase": phase,                   # "awaiting_code"
        "attempts": attempts,
        "expires_at": (now_utc() + timedelta(minutes=expires_in_minutes)).isoformat(),
        "updated_at": now_utc().isoformat(),
    }, merge=True)

def clear_auth_session(e164: str):
    database.collection("auth_sessions").document(e164).delete()
