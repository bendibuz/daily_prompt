from datetime import datetime
from app.models import UserMessage
from app.services.data_service import save_user_response

def handle_incoming_msg(form: dict):
    from_num = form.get("From")
    message_body = form.get("Body") or ""
    payload = UserMessage(
        user_id=from_num,
        message=message_body,
        phone_number=from_num,
        timestamp=datetime.now(datetime.timezone.utc)
    )
    save_user_response(payload)
    return {"ok": True}