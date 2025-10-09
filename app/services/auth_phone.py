# app/services/auth_phone.py
from typing import Optional

from firebase_admin import auth, firestore
from twilio.rest import Client

from app.config import settings
from app.adapters.firebase_client import get_firebase_client
from app.utilities import utcnow, normalize_to_e164




# --- Initialization ----------------------------------------------------------

def _get_twilio_client() -> Client:
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        raise RuntimeError("Missing Twilio credentials (TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN).")
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def _get_verify_sid() -> str:
    if not settings.TWILIO_VERIFY_SID:
        raise RuntimeError("Missing TWILIO_VERIFY_SID in config.")
    return settings.TWILIO_VERIFY_SID

# Ensure Firebase Admin is initialized before getting a Firestore client
get_firebase_client()
database = firestore.client()

twilio_client = _get_twilio_client()
verify_sid = _get_verify_sid()


def start_phone_verification(phone_number: str) -> None:
    twilio_client.verify.v2.services(verify_sid).verifications.create(
        to=phone_number, channel="sms"
    )

def check_phone_verification(phone_number: str, code: str) -> bool:
    res = twilio_client.verify.v2.services(verify_sid).verification_checks.create(
        to=phone_number, code=code
    )
    return res.status == "approved"

def get_or_create_user_for_phone(phone_e164: str, display_name: Optional[str] = None) -> str:
    try:
        u = auth.get_user_by_phone_number(phone_e164)
        uid = u.uid
    except auth.UserNotFoundError:
        u = auth.create_user(phone_number=phone_e164, display_name=display_name or None)
        uid = u.uid
    # Ensure a Firestore profile exists
    user_ref = database.collection("users").document(uid)
    snap = user_ref.get()
    now = utcnow()
    if not snap.exists:
        user_ref.set({
            "user_id": uid,
            "display_name": display_name,
            "email": None,
            "phones": [phone_e164],
            "timezone": "America/Chicago",
            "activated": True,
            "created_at": now,
            "updated_at": now,
        })
    else:
        # keep phones list in sync
        data = snap.to_dict() or {}
        phones = set(data.get("phones") or [])
        if phone_e164 not in phones:
            phones.add(phone_e164)
            user_ref.set({"phones": list(phones), "updated_at": now}, merge=True)
    return uid

def bind_phone_to_user(phone_e164: str, user_id: str) -> None:
    phone_ref = database.collection("phone_bindings").document(phone_e164)
    user_ref = database.collection("users").document(user_id)
    @firestore.transactional
    def tx_fn(tx):
        phone_doc = tx.get(phone_ref)
        print(phone_doc)
        if phone_doc and phone_doc.exists:
            data = phone_doc.to_dict() or {}
            existing_uid = data.get("user_id")
            # simplest safe policy: if bound to a different user and not released, block
            if existing_uid and existing_uid != user_id and not data.get("released_at"):
                raise ValueError("Phone number already bound to another user")
        tx.set(phone_ref, {
            "user_id": user_id,
            "verified": True,
            "bound_at": firestore.SERVER_TIMESTAMP,
            "released_at": None,
            "last_seen": firestore.SERVER_TIMESTAMP,
            "labels": ["primary"]
        }, merge=True)
        # ensure user doc has phone listed
        user_doc = tx.get(user_ref)
        phones = set((user_doc.to_dict() or {}).get("phones") or [])
        if phone_e164 not in phones:
            phones.add(phone_e164)
            tx.set(user_ref, {"phones": list(phones), "updated_at": firestore.SERVER_TIMESTAMP}, merge=True)
    tx = database.transaction()
    tx_fn(tx)
