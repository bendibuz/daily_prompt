from firebase_admin import firestore, auth, initialize_app, credentials
from app.models.models import UserDoc, Goal
from app.adapters.firebase_client import get_firebase_client
from datetime import datetime
from zoneinfo import ZoneInfo


get_firebase_client()
db = firestore.client()

# def create_user(user: User):
#     # TODO: validate user phone number here?
#     # TODO: validate any other user info here
#     doc_ref = db.collection('users').document(user.phone_number)
#     doc_ref.set(user)
#     pass

def create_user_v2(user: UserDoc):
    try:
        input_phone = user.phone_number
        rec = auth.create_user(
            email=user.email,
            password=user.password,
            display_name=user.display_name,
            phone_number=user.phone_number
            # created_at = datetime.now,
            # updated_at = datetime.now
        )
        print(f'Successfully created new user for phone number {input_phone}')
        return rec
    except Exception as e:
        print(f'Error creating user: {e}')


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