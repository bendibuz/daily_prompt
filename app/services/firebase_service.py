# firebase_service.py (key fixes)
from firebase_admin import firestore, auth
from app.models.models import UserDoc, Goal, DeviceGoalChange
from datetime import datetime, timezone
import phonenumbers
from dataclasses import asdict
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict

from app.adapters.firebase_client import get_firebase_client
get_firebase_client()
db = firestore.client()

def get_today_date_key(user: UserDoc) -> str:
    tz = ZoneInfo(user.timezone or "America/Chicago")
    return datetime.now(tz).date().isoformat()

def normalize_to_e164(phone_number: str, default_region: str = "US") -> str:
    num = phonenumbers.parse(phone_number, default_region)
    if not phonenumbers.is_valid_number(num):
        raise ValueError("Invalid phone number")
    return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)

def get_user_data(user_id: str) -> Optional[UserDoc]:
    if user_id is None:
        return "No User ID Provided!"
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise ValueError("User not found")
    user_data = user_doc.to_dict() or {}
    user = UserDoc(**user_data)
    return user


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

def pair_user_device(user: UserDoc, device_id: str) -> None:
    ts = datetime.now(timezone.utc)

    # 1. Write device under the user
    db.collection("users") \
      .document(user.user_id) \
      .collection("devices") \
      .document(device_id) \
      .set({
          "device_id": device_id,
          "created_at": ts,
          "updated_at": ts,
          "last_seen": ts,
          "device_name": "Digidoit v0.1"
      })

    # 2. Create the top-level mapping (fast lookup from ESP → user)
    db.collection("device_map") \
      .document(device_id) \
      .set({
          "user_id": user.user_id,
          "updated_at": ts,
      })
    
def get_user_from_device(device_id: str) -> UserDoc:
    doc = db.collection("device_map").document(device_id).get()
    if not doc.exists:
        raise ValueError(f"Device {device_id} not found")
    user_id = doc.get("user_id")
    if not user_id:
        raise ValueError(f"Device {device_id} not currently paired to a user.")
    user = get_user_data(user_id)
    if not user:
        raise ValueError(f"User '{user_id}' not found or not valid.")
    return user

def get_unsynced_goals_for_user(user: UserDoc):
    date_key = get_today_date_key(user)
    goals_ref = (
        db.collection("users")
          .document(user.user_id)
          .collection("days")
          .document(date_key)  # or however you access today
          .collection("goals")
    )
    docs = goals_ref.where("synced_to_device", "==", False).stream()
    return [d.to_dict() | {"id": d.id} for d in docs]

def mark_goals_synced(user: UserDoc, goals: list[dict]) -> None:
    date_key = get_today_date_key(user)
    if not goals:
        return
    batch = db.batch()
    for g in goals:
        goal_id = g["id"]
        goal_ref = (
            db.collection("users")
              .document(user.user_id)
              .collection("days")
              .document(date_key)
              .collection("goals")
              .document(goal_id)
        )
        batch.update(goal_ref, {"synced_to_device": True})
    batch.commit()

def apply_device_changes(user: UserDoc, changes: List[DeviceGoalChange]) -> None:
    if not changes:
        return

    date_key = get_today_date_key(user)
    batch = db.batch()

    for change in changes:
        goal_ref = (
            db.collection("users")
              .document(user.user_id)
              .collection("days")
              .document(date_key)
              .collection("goals")
              .document(change.id)
        )
        batch.update(goal_ref, {"completed": change.completed})

    batch.commit()

def sync_user_goals(device_id: str, changes: List[DeviceGoalChange]) -> List[Dict]:
    """
    Main sync workflow for a device:
      1) resolve user
      2) apply device-side completion changes
      3) fetch unsynced goals
      4) mark them synced
      5) return the goals to send to device
    """
    user = get_user_from_device(device_id)
    print(user.user_id)
    apply_device_changes(user, changes)
    unsynced_goals = get_unsynced_goals_for_user(user)
    mark_goals_synced(user, unsynced_goals)
    return unsynced_goals
    