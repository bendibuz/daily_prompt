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

def add_new_user(user: UserDoc):
    formatted_phone = standardize_phone(user.phone_number) if user.phone_number else None
    rec = auth.create_user(
        email=user.email,
        password=user.password,
        display_name=user.display_name,
        phone_number=formatted_phone,
    )

    uid = rec.uid
    now = datetime.now(timezone.utc)
    user_doc = {
        "uid": uid,
        "email": user.email,
        "display_name": user.display_name,
        "phone_number": formatted_phone,
        "created_at": now,
        "updated_at": now,
        "activated": False,
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

def create_goals_entry(goals: dict):
    goals = dicts_to_goals(goals)
    for goal in goals:
        new_goal = db.collection("goals").add(goal)
        print(f"Added goal with id {new_goal.id}")
    pass

def get_today_goals_for_user(user: UserDoc) -> list[Goal]:
    """
    Fetch today's goals for the given user.
     users/{phone}/days/{YYYY-MM-DD} (field: "goals": [ {...}, ... ])
    Returns a list[Goal]. Empty list if nothing is found.
    """
    tz = ZoneInfo("America/Chicago")
    date_key = datetime.now(tz).date().isoformat()

    user_day_ref = (
        db.collection("users")
          .document(user.phone_number)
          .collection("days")
          .document(date_key)
    )
    doc = user_day_ref.get()
    if doc.exists:
        data = doc.to_dict() or {}
        return dicts_to_goals(data.get("goals"))

    return []