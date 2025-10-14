# firebase_service.py (key fixes)
from firebase_admin import firestore, auth
from app.models.models import UserDoc, Goal
from datetime import datetime, timezone
import phonenumbers
from dataclasses import asdict
from zoneinfo import ZoneInfo

from app.adapters.firebase_client import get_firebase_client
get_firebase_client()
db = firestore.client()

def normalize_to_e164(phone_number: str, default_region: str = "US") -> str:
    num = phonenumbers.parse(phone_number, default_region)
    if not phonenumbers.is_valid_number(num):
        raise ValueError("Invalid phone number")
    return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)


def add_new_user(user: UserDoc, *, raw_password: str | None = None, phone_number: str | None = None):
    e164 = normalize_to_e164(phone_number) if phone_number else None
    rec = auth.create_user(
        email=user.email,
        password=raw_password or None,
        display_name=user.display_name,
        phone_number=e164,
    )
    uid = rec.uid
    now = datetime.now(timezone.utc)

    user_doc = {
        "user_id": uid,
        "email": user.email,
        "display_name": user.display_name,
        "phones": [e164] if e164 else [],
        "timezone": user.timezone,
        "activated": False,
        "created_at": now,
        "updated_at": now,
    }

    try:
        db.collection("users").document(uid).set(user_doc)
        if e164:
            db.collection("phone_bindings").document(e164).set({
                "user_id": uid,
                "verified": True,
                "bound_at": now,
                "released_at": None,
                "last_seen": now,
                "labels": ["primary"]
            }, merge=True)
    except Exception as e:
        try:
            auth.delete_user(uid)
        finally:
            raise RuntimeError(f"Failed to create Firestore user; rolled back Auth. Details: {e}")

    return {"uid": uid}

def dicts_to_goals(items) -> list[Goal]:
    goals = []
    for g in items or []:
        goals.append(
            Goal(
                goal_text=g.get("goal_text", ""),
                points=int(g.get("points", 0)),
                complete=bool(g.get("complete", False)),
            )
        )
    return goals

def create_goals_entry(goals: list[dict], user: UserDoc) -> None:
    goals = dicts_to_goals(goals)
    tz = ZoneInfo(user.timezone or "America/Chicago")
    date_key = datetime.now(tz).date().isoformat()
    user_day_ref = db.collection("users").document(user.user_id).collection("days").document(date_key)
    for goal in goals:
        print(f'💾 Creating goal for user {user.user_id}: {goal}')
        user_day_ref.collection("goals").add(asdict(goal))

def get_today_goals_for_user(user: UserDoc) -> list[Goal]:
    tz = ZoneInfo(user.timezone or "America/Chicago")
    date_key = datetime.now(tz).date().isoformat()
    user_day_ref = db.collection("users").document(user.user_id).collection("days").document(date_key)
    goals_snap = user_day_ref.collection("goals").get()
    goal_dicts = [doc.to_dict() for doc in goals_snap]
    return dicts_to_goals(goal_dicts)

def get_today_goal_refs(user: UserDoc) -> list[firestore.DocumentReference]:
    tz = ZoneInfo(user.timezone or "America/Chicago")
    date_key = datetime.now(tz).date().isoformat()
    user_day_ref = db.collection("users").document(user.user_id).collection("days").document(date_key)
    goals_snap = user_day_ref.collection("goals").get()
    return [doc.reference for doc in goals_snap]