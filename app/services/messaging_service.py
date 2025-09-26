# messaging_service.py
from dataclasses import asdict, dataclass, field
from typing import Optional, List, Dict, Any
from firebase_admin import firestore
from twilio.twiml.messaging_response import MessagingResponse

from app.adapters.firebase_client import get_firebase_client

from app.utilities import utcnow, normalize_to_e164

# --- init --------------------------------------------------------------------
get_firebase_client()
db = firestore.client()

# --- lookups ---------------------------------------------------------------------
def resolve_user_id_by_phone(e164: str) -> Optional[str]:
    """
    Preferred: O(1) lookup in phone_bindings/{+E164} → { user_id }.
    Fallback: users where 'phones' array contains the E.164 string.
    """
    # 1) phone_bindings collection (single doc read)
    pb_ref = db.document(f"phone_bindings/{e164}")
    pb_doc = pb_ref.get()
    if pb_doc.exists:
        data = pb_doc.to_dict() or {}
        uid = data.get("user_id")
        if uid:
            return uid

    # 2) fallback: users with phones array (array-contains requires exact string)
    snap = (
        db.collection("users")
        .where("phones", "array_contains", e164)
        .limit(1)
        .get()
    )
    if snap:
        return snap[0].id  # assuming docId == uid

    return None

# --- persistence --------------------------------------------------------------
def save_raw_message(
    message_body: str,
    from_number: str,
    *,
    user_id: Optional[str],
    to_number: Optional[str] = None,
    sid: Optional[str] = None,
) -> str:
    """
    Persist the raw inbound message (immutable log).
    If you pass Twilio MessageSid, we use it as the doc id for idempotency.
    """
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
        # Idempotent write
        ref = db.collection("messages").document(sid)
        if not ref.get().exists:
            ref.set(doc)
        return ref.id
    else:
        _, ref = db.collection("messages").add(doc)
        return ref.id

def save_user_response(user_id: Optional[str], parsed: Dict[str, Any], *, source_message_sid: Optional[str], from_number: str) -> str:
    """
    Save the structured interpretation (separate from raw 'messages').
    """
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

# --- parsing ------------------------------------------------------------------
def parse_response_text(text: str) -> Dict[str, Any]:
    """
    Very simple DSL:
      - Split on ';'
      - Trim whitespace, drop empties
      - Recognize optional prefixes: 'done:', 'goal:', 'note:'
    """
    raw_items = [s.strip() for s in (text or "").split(";")]
    items = [s for s in raw_items if s]

    goals: List[Dict[str, Any]] = []
    notes: List[str] = []
    done: List[str] = []

    for item in items:
        low = item.lower()
        if low.startswith("done:"):
            done.append(item[5:].strip())
        elif low.startswith("goal:"):
            goals.append({"title": item[5:].strip(), "status": "new"})
        elif low.startswith("note:"):
            notes.append(item[5:].strip())
        else:
            goals.append({"title": item, "status": "new"})

    return {
        "goals": goals,
        "done": done,
        "notes": notes,
        "item_count": len(items),
        "parser_version": "v1",
    }

# --- high-level orchestrator --------------------------------------------------
def handle_incoming_message(
    message: str,
    phone_number: str,
    *,
    to_number: Optional[str] = None,
    sid: Optional[str] = None,           # Twilio MessageSid if available
    default_region: str = "US",
) -> Dict[str, Any]:
    """
    Main entrypoint called by your route handler.
    Returns a dict describing routing/next-steps; routes can decide TwiML.
    """
    e164 = normalize_to_e164(phone_number, default_region=default_region)

    # Handle STOP/UNSUBSCRIBE keywords (per CTIA guidelines)
    text_lower = (message or "").strip().lower()
    if text_lower in {"stop", "unsubscribe", "cancel", "quit"}:
        db.collection("subscriptions").document(e164).set({"status": "unsubscribed", "updated_at": utcnow().isoformat()}, merge=True)
        return {
            "user_id": resolve_user_id_by_phone(e164),
            "from_number": e164,
            "message_id": save_raw_message(message_body=message, from_number=e164, user_id=None, to_number=to_number, sid=sid),
            "response_id": None,
            "next_actions": [],
            "parsed": {}
        }
    
    user_id = resolve_user_id_by_phone(e164)

    message_id = save_raw_message(
        message_body=message,
        from_number=e164,
        user_id=user_id,
        to_number=to_number,
        sid=sid,
    )

    parsed = {}
    try:
        parsed = parse_response_text(message)
    except Exception:
        parsed = {}

    response_id = save_user_response(
        user_id=user_id,
        parsed=parsed,
        source_message_sid=sid,
        from_number=e164,
    )

    next_actions: List[str] = []
    if user_id is None:
        next_actions.append("start_user_claim_flow")  # reply asking to link/verify
    else:
        has_goals = bool(parsed.get("goals"))
        has_done = bool(parsed.get("done"))
        if has_goals:
            next_actions.append("create_or_update_goals")
        if has_done:
            next_actions.append("mark_goals_done")
        if not (has_goals or has_done):
            next_actions.append("send_help_text")

    return {
        "user_id": user_id,
        "from_number": e164,
        "message_id": message_id,
        "response_id": response_id,
        "next_actions": next_actions,
        "parsed": parsed,
    }

def build_twilml_for_result(result: Dict[str, Any]) -> str:
    """
    Small helper if you prefer to return TwiML directly from the route.
    Adjust copy to your tone/UX.
    """
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
    if not resp.messages:
        resp.message("Sorry, didn't quite get that. Send 'help' for tips.")

    return str(resp)