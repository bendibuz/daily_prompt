from app.services.messaging_service import handle_incoming_message, build_twilml_for_result
from app.models.models import UserDoc
from twilio.twiml.messaging_response import MessagingResponse
from fastapi import APIRouter, Request, Response

router = APIRouter()

from app.services.firebase_service import add_new_user

# Test route
@router.get("/")
def root_response():
    return("Hello World!")

#Incoming SMS webhook
@router.post("/webhook/sms")
async def receive_sms(request: Request):
    form = await request.form()
    phone_number = form.get("From")
    message_body = form.get("Body")
    to_number = form.get("To")
    message_sid = form.get("MessageSid")

    result = handle_incoming_message(
        message=message_body,
        phone_number=phone_number,
        to_number=to_number,
        sid=message_sid
    )

    twiml = build_twilml_for_result(result)
    return Response(content=twiml, media_type="application/xml")

@router.post("/create_user")
def create_user(user: UserDoc):  # align type with your service
    from app.services.firebase_service import add_new_user
    return add_new_user(user)