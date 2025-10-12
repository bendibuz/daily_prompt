# messaging_service.py
from typing import Optional, List, Dict, Any
from enum import Enum
from firebase_admin import firestore
from twilio.twiml.messaging_response import MessagingResponse
from app.adapters.firebase_client import get_firebase_client
from app.utilities import utcnow, normalize_to_e164
from app.services.auth_phone import get_or_create_user_for_phone, bind_phone_to_user
from app.services.utilities.parser import parse_message


# Receive a message
# Check if the user exists based on phone number
# If they don't exist, prompt for signup 🌞
# If they do exist, parse the response and add actions
# Commit the actions
# Build a response
# Send response
# Done!


'''
def handle_incoming_message(msg, phone, *, sid=None, to_number=None, region="US"):
    e164 = normalize_to_e164(phone, default_region=region)
    user_id = resolve_user_id_by_phone(e164)

    # 1) persist raw (idempotent if sid)
    save_raw_message(msg, e164, user_id=user_id, to_number=to_number, sid=sid)

    # 2) parse once
    try:
        parsed = parse_message(msg)       # -> MessageActions
    except Exception:
        parsed = None
    parsed_dict = to_dict(parsed)

    # 3) persist parsed
    save_user_response(user_id=user_id, parsed=parsed_dict, source_message_sid=sid, from_number=e164)

    # 4) route (pure)
    actions = route_actions(user_id=user_id, parsed=parsed)   # returns List[Actions]

    # 5) commit (side effects live here)
    replies = commit_actions(
        e164, user_id, actions,
        parsed=parsed_dict, raw_message=msg, source_sid=sid
    )

    # 6) render
    if not replies:
        return build_response(["Sorry, didn’t catch that. Send 'help' for tips."])
    return build_response(replies)
'''

get_firebase_client()
db = firestore.client()

def build_response(reply_messages):
    concat = "\n".join(str(m) for m in reply_messages)
    resp = MessagingResponse()
    resp.message(concat)
    return resp

def prompt_signup(**kwargs):
    resp = MessagingResponse()
    reply = resp.message("Welcome! Reply YES to link this phone to a new account.")
    return reply
    # return Response(content=str(resp), media_type="application/xml")

def signup(**kwargs):
    phone_number = kwargs.get("phone_number")
    e164 = normalize_to_e164(phone_number)
    user_id = get_or_create_user_for_phone(e164)
    bind_phone_to_user(e164, user_id)
    resp = MessagingResponse()
    reply = resp.message("You are all set! You can now text me goals and updates any time.")
    return reply
    # return Response(content=str(resp), media_type="application/xml")
        
def stop_service(phone_number, user_id, **kwargs):
    pass
def help_request(phone_number, user_id, **kwargs):
    pass
def send_help(phone_number, user_id, **kwargs):
    pass

# These two can be added together into one message
def set_goals(phone_number, user_id, **kwargs):
    pass
def mark_done(phone_number, user_id, **kwargs):
    pass

# def unknown(phone_number, user_id, **kwargs):
#     pass

class Actions(Enum):
    SIGNUP = signup
    PROMPT_SIGNUP = prompt_signup
    STOP = stop_service
    HELP_REQ = help_request
    SEND_HELP = send_help
    SET_GOALS = set_goals
    MARK_DONE = mark_done
    # UNKNOWN = unknown

def commit_actions(phone_number, user_id, actions: List[Actions], **kwargs) -> bool:
    reply_messages = []
    for action in actions:
        try:
            reply = Actions[action.name].value(phone_number, user_id, **kwargs)
        except Exception as e:
            reply = None
        if reply:
            reply_messages.append(reply)
    return reply_messages


# 🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲🪲 Beatlemania
def resolve_user_id_by_phone(e164: str) -> Optional[str]:
    binding_ref = db.document(f"phone_bindings/{e164}")
    print(binding_ref)
    binding_doc = binding_ref.get()
    print(binding_doc)

    # Indexed shortcut
    if binding_doc.exists:
        data = binding_doc.to_dict() or {}
        print(data)
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
    payload = {
        "user_id": user_id,
        "from_number": from_number,
        "parsed": parsed,
        "parse_status": "parsed" if parsed else "failed",
        "source_message_sid": source_message_sid,
        "created_at": utcnow().isoformat(),
    }
    _, ref = db.collection("user_responses").add(payload)
    return ref.id


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

    save_raw_message(
        message_body=message,
        from_number=e164,
        user_id=user_id,
        to_number=to_number,
        sid=sid,
    )

    try:
        parsed = parse_message(message)
    except Exception:
        parsed = {}

    save_user_response(
        user_id=user_id,
        parsed=parsed,
        source_message_sid=sid,
        from_number=e164,
    )

    next_actions = parsed
    next_actions: List[Actions] = []

    # actions = route_actions(user_id, parsed)

    if user_id is None:
        next_actions.append(Actions.PROMPT_SIGNUP)  # reply asking to link/verify
    else:
        parsed.get("signup") and next_actions.append(Actions.SIGNUP)
        parsed.get("goals") and next_actions.append(Actions.SET_GOALS)
        parsed.get("done") and next_actions.append(Actions.MARK_DONE)
        if len(next_actions) == 0 or parsed == {}:
            next_actions.append(Actions.HELP_REQ)

    reply_messages = commit_actions(e164, user_id, next_actions)
    
    if reply_messages == []:
        resp = MessagingResponse()
        resp.message("Sorry, didn't quite get that. Send 'help' for tips.")
        return resp
    else:
        compiled_response = build_response(reply_messages)
        return compiled_response

    # return {
    #     "user_id": user_id,
    #     "from_number": e164,
    #     "message_id": message_id,
    #     "response_id": response_id,
    #     "next_actions": next_actions,
    #     "parsed": parsed,
    # }

def build_twilml_for_result(result: Dict[str, Any]) -> str:
    resp = MessagingResponse()

    if result["user_id"] is None:
        resp.message("Hello! Welcome to Digidoit. Looks like its your first time here. Reply YES to link this phone to a new account!")
        return str(resp)

    actions = result.get("next_actions", [])
    parsed = result.get("parsed", {})

    if "create_or_update_goals" in actions:
        titles = [g["title"] for g in parsed.get("goals", [])]
        if titles:
            resp.message("Got it! Goals logged:\n- " + "\n- ".join(titles))

    if "mark_goals_done" in actions:
        dones = parsed.get("done", [])
        if dones:
            resp.message("Nice work! Marked done:\n- " + "\n- ".join(dones))

    if actions == ["send_help_text"]:
        resp.message("Try sending goals like: 'goal: workout 30m; goal: read 10 pages' or mark done like: 'done: workout'.")

    # If no messages were added above, add a generic thank you
    if not resp.message:
        resp.message("Sorry, didn't quite get that. Send 'help' for tips.")

    return str(resp)
