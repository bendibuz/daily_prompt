from firebase_admin import firestore, auth, initialize_app, credentials
from app.models.models import UserDoc, Goal
from app.adapters.firebase_client import get_firebase_client
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from phonenumberfmt import format_phone_number


get_firebase_client()
db = firestore.client()

def standardize_phone(phone_number):
    formatted = format_phone_number(phone_number, "US")
    return formatted

def create_user(user: UserDoc):
    # 1) Normalize input
    formatted_phone = standardize_phone(user.phone_number) if user.phone_number else None

    # 2) Create Auth user
    rec = auth.create_user(
        email=user.email,
        password=user.password,
        display_name=user.display_name,
        phone_number=formatted_phone,
    )
    uid = rec.uid
    print(uid)
    # 3) Create Firestore doc using uid as the document ID
    now = datetime.now(timezone.utc)
    user_doc = {
        "uid": uid,
        "email": user.email,
        "display_name": user.display_name,
        "phone_number": formatted_phone,
        # "created_at": now,
        # "updated_at": now,
        # put app-specific defaults here
        # "status": "active",
        # "onboarding_complete": False,
    }

    try:
        db.collection("users").document(uid).set(user_doc)
    except Exception as e:
        # rollback to avoid dangling Auth users without a Firestore profile
        print(f"Failed with exception {e}")
        try:
            auth.delete_user(uid)
        finally:
            raise RuntimeError(f"Failed to create Firestore user doc; rolled back Auth user. Details: {e}")

    return {"uid": uid}


# Goals


def dicts_to_goals(items) -> list[Goal]:
    goals = []
    for g in items or []:
        # Be forgiving about missing fields
        goals.append(
            Goal(
                goal_text=g.get("goal_text", ""),
                points=int(g.get("points", 0)),
                complete=bool(g.get("complete", False)),
            )
        )
    return goals


def create_goals_entry():
    pass

def get_today_goals_for_user(user: UserDoc) -> list[Goal]:
    """
    Fetch today's goals for the given user.
     users/{phone}/days/{YYYY-MM-DD} (field: "goals": [ {...}, ... ])
    Returns a list[Goal]. Empty list if nothing is found.
    """
    tz = ZoneInfo("America/Chicago")
    date_key = datetime.now(tz).date().isoformat()

    # Path 1: nested under the user doc
    user_day_ref = (
        db.collection("users")
          .document(user.phone_number)
          .collection("days")
          .document(date_key)
    )
    snap = user_day_ref.get()
    if snap.exists:
        data = snap.to_dict() or {}
        return dicts_to_goals(data.get("goals"))

    # Nothing found
    return []