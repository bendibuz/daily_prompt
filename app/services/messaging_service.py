# messaging_service.py
from typing import Optional, List, Dict, Any
from enum import Enum
from firebase_admin import firestore
from twilio.twiml.messaging_response import MessagingResponse
from app.adapters.firebase_client import get_firebase_client
from app.utilities import utcnow, normalize_to_e164
from app.services.auth_phone import get_or_create_user_for_phone, bind_phone_to_user
from app.services.utilities.parser import parse_message
from dataclasses import asdict
from app.services.firebase_service import create_goals_entry, get_today_goals_for_user
from app.models.models import UserDoc, Goal

not_found_msg = "👋 Hello! Please sign up first by texting 'signup'."

get_firebase_client()
db = firestore.client()

def get_user_data(user_id: str) -> Optional[UserDoc]:
    if user_id is None:
        return not_found_msg
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return not_found_msg
    user_data = user_doc.to_dict() or {}
    user = UserDoc(**user_data)
    return user

def build_response(reply_messages):
    concat = "\n".join(str(m) for m in reply_messages)
    resp = MessagingResponse()
    resp.message(str(concat))
    return resp

def prompt_signup(phone_number, user_id, **kwargs):
    print(f'❔ Prompting signup for {phone_number}, user_id={user_id}')
    e164 = normalize_to_e164(phone_number)
    user_id = get_or_create_user_for_phone(e164)
    if user_id:
        return "Welcome! Reply YES to link this phone to a new account."
    else:
        return "Error creating user account. Please try again later."

def signup(phone_number, user_id, **kwargs):
    print(f'📝 Signing up {phone_number}, user_id={user_id}')
    e164 = normalize_to_e164(phone_number)
    if user_id:
        bind_phone_to_user(e164, user_id)
        return "You are all set! You can now text me goals and updates any time."
    prompt_signup(phone_number, user_id)
    # return Response(content=str(resp), media_type="application/xml")
        
def stop_service(phone_number, user_id, **kwargs):
    return "Stop service"
def help_request(phone_number, user_id, **kwargs):
    return "Didn't get that... need help? Send 'help' for tips."
def send_help(phone_number, user_id, **kwargs):
    return "Available commands are x, y, z"

# These two can be added together into one message
def set_goals(phone_number, user_id, **kwargs):
    user = get_user_data(user_id)

    goals = kwargs.get("new_goals", [])
    try:
        create_goals_entry(goals=goals, user=user)
    except Exception as e:
        print(f'⚠️ Error creating goals: {e}')
        return "⚠️ Error saving goals. Please try again."
    return "Goals set"

def mark_done(phone_number, user_id, **kwargs):
    user = get_user_data(user_id)
    goals = kwargs.get("mark_done", [])
    today_goals = get_today_goals_for_user(user)
    goal_texts = [g.goal_text for g in today_goals]
    verified_complete = []
    for goal in goals:
        if goal in goal_texts:
            idx = goal_texts.index(goal)
            today_goals[idx].complete = True
            verified_complete.append(goal)
    if len(verified_complete) == 0:
        return "No matching goals found to mark as done."
    return f"Marked as done: {', '.join(verified_complete)}"


class Actions(Enum):
    SIGNUP = signup
    PROMPT_SIGNUP = prompt_signup
    STOP = stop_service
    HELP_REQ = help_request
    SEND_HELP = send_help
    SET_GOALS = set_goals
    MARK_DONE = mark_done
    # UNKNOWN = unknown


def commit_actions(phone_number, user_id, actions, **kwargs) -> bool:

    reply_messages = []
    for action in actions:
        try:
            fn = action.value if isinstance(action, Actions) else action
            reply = fn(phone_number, user_id, **kwargs)
            print(f'⏩ Action: {action}, ⏪ Reply: {reply}')
        except Exception as e:
            print('⚠️ ERROR when committing actions:', e)
            reply = None
        if reply:
            reply_messages.append(reply)

    print(f'💬 Reply messages: {reply_messages}')
    return reply_messages


# 🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲 Beatlemania
def resolve_user_id_by_phone(e164: str) -> Optional[str]:
    binding_ref = db.document(f"phone_bindings/{e164}")
    binding_doc = binding_ref.get()

    # Indexed shortcut
    if binding_doc.exists:
        data = binding_doc.to_dict() or {}
        uid = data.get("user_id")
        if uid:
            return uid
    
    # Slower route
    snap = (
        db.collection("users")
        .where("phones", "array_contains", e164)
        .limit(1)
        .get()
    )

    if snap:
        return snap[0].id  # assuming docId == uid

    return None

# 🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞🐞 Ladybug
def save_raw_message(
    message_body: str,
    from_number: str,
    *,
    user_id: Optional[str],
    to_number: Optional[str] = None,
    sid: Optional[str] = None,
) -> str:

    doc = {
        "body": message_body,
        "from": from_number,
        "to": to_number,
        "user_id": user_id,
        "received_at": utcnow().isoformat(),
        "sid": sid,
        "source": "twilio",
    }

    if sid:
        ref = db.collection("messages").document(sid)
        if not ref.get().exists:
            ref.set(doc)
        return ref.id
    else:
        _, ref = db.collection("messages").add(doc)
        return ref.id

def save_user_response(user_id: Optional[str], parsed: Dict[str, Any], *, source_message_sid: Optional[str], from_number: str) -> str:
    print(f'🔥 {asdict(parsed)}')
    payload = {
        "user_id": user_id,
        "from_number": from_number,
        "parsed": asdict(parsed),
        "parse_status": "parsed" if parsed else "failed",
        "source_message_sid": source_message_sid,
        "created_at": utcnow().isoformat(),
    }
    _, ref = db.collection("user_responses").add(payload)
    return ref.id

def check_user_phone_binding(e164: str, user_id: str) -> bool:
    binding_ref = db.document(f"phone_bindings/{e164}")
    binding_doc = binding_ref.get()
    if binding_doc.exists:
        data = binding_doc.to_dict() or {}
        existing_uid = data.get("user_id")
        if existing_uid == user_id:
            return True
    return False

def handle_incoming_message(
    message: str,
    phone_number: str,
    *,
    to_number: Optional[str] = None,
    sid: Optional[str] = None,           # Twilio MessageSid if available
    default_region: str = "US",
) -> Dict[str, Any]:
    
    e164 = normalize_to_e164(phone_number, default_region=default_region)  
    user_id = resolve_user_id_by_phone(e164)
    phone_binding_exists = check_user_phone_binding(e164, user_id) if user_id else False
    print(f'🌞 Normalized {phone_number} to {e164}, user_id={user_id}, binding exists={phone_binding_exists}')

    save_raw_message(
        message_body=message,
        from_number=e164,
        user_id=user_id,
        to_number=to_number,
        sid=sid,
    )

    try:
        parsed = parse_message(message)
        actions_dict = asdict(parsed)
    except Exception:
        parsed = {}

    save_user_response(
        user_id=user_id,
        parsed=parsed,
        source_message_sid=sid,
        from_number=e164,
    )

    next_actions: List[Actions] = []

    # actions = route_actions(user_id, parsed)

    if user_id is None:
        next_actions.append(Actions.PROMPT_SIGNUP)  # reply asking to link/verify
    else:
        if phone_binding_exists is False:
            parsed.signup and next_actions.append(Actions.SIGNUP)  # reply asking to link/verify    
        else:
            if(len(parsed.new_goals) > 0): next_actions.append(Actions.SET_GOALS)
            if(len(parsed.mark_done) > 0): next_actions.append(Actions.MARK_DONE)
            if len(next_actions) == 0 or parsed == {}:
                next_actions.append(Actions.HELP_REQ)

    reply_messages = commit_actions(e164, user_id, next_actions, **actions_dict)
    
    if len(reply_messages) == 0:
        resp = MessagingResponse()
        resp.message("Sorry, didn't quite get that. Send 'help' for tips.")
        return resp
    else:
        compiled_response = build_response(reply_messages)
        return compiled_response
