from app.models.models import UserDoc
from twilio.twiml.messaging_response import MessagingResponse
from fastapi import APIRouter, Request, Response, HTTPException
from app.services.messaging_service import (
    resolve_user_id_by_phone as resolve_user_identifier_by_phone,
    handle_incoming_message, 
    build_twilml_for_result,
)
from app.services.auth_phone import get_or_create_user_for_phone, bind_phone_to_user
from app.utilities import normalize_to_e164
import os
from twilio.request_validator import RequestValidator
import logging
from app.config import settings

router = APIRouter()
log = logging.getLogger("routes.sms")


def _external_url_for_validation(request: Request) -> str:
    scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
    host   = request.headers.get("x-forwarded-host")  or request.headers.get("host") or request.url.netloc
    path_q = request.url.path + (("?" + request.url.query) if request.url.query else "")
    return f"{scheme}://{host}{path_q}"

async def validate_twilio_request(request: Request):
    form = await request.form()  # Twilio signs form fields

    # Read from settings first (loads .env), fall back to os.getenv
    auth_token = settings.TWILIO_AUTH_TOKEN or os.getenv("TWILIO_AUTH_TOKEN")
    if not auth_token:
        log.error("TWILIO_AUTH_TOKEN not found via settings or environment")
        raise HTTPException(status_code=500, detail="Missing TWILIO_AUTH_TOKEN")

    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        log.warning("Missing X-Twilio-Signature header")
        raise HTTPException(status_code=403, detail="Missing Twilio signature header")

    url_for_validation = _external_url_for_validation(request)
    params = dict(form)

    if not RequestValidator(auth_token).validate(url_for_validation, params, signature):
        log.warning("Twilio signature validation failed for %s", url_for_validation)
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    return form

@router.get("/")
def root_response():
    return "Hello World!"

# @router.post("/webhook/sms")  # temp endpoint
# async def receive_sms_test(request: Request):
#     raw = (await request.body()).decode("utf-8", errors="ignore")
#     print("RAW:", raw)
#     form = await request.form()
#     print("FORM:", dict(form))
#     resp = MessagingResponse()
#     resp.message("pong")
#     return Response(content=str(resp), media_type="application/xml")

@router.post("/webhook/sms")
async def receive_sms(request: Request):
    try:
        form = await validate_twilio_request(request)
        raw_from = form.get("From", "")
        body = (form.get("Body") or "").strip()
        to_number = form.get("To", "")
        message_sid = form.get("MessageSid")

        try:
            e164 = normalize_to_e164(raw_from)
        except Exception:
            resp = MessagingResponse()
            resp.message("We could not read your phone number. Please try again.")
            log.warning("Bad From: %r sid=%r", raw_from, message_sid)
            return Response(content=str(resp), media_type="application/xml", status_code=200)

        # Optional: subscription keywords before anything else
        lower = body.lower()
        if lower in {"stop", "unsubscribe", "cancel", "quit"}:
            # mark unsubscribed if you track it; still ack per carrier rules
            resp = MessagingResponse()
            resp.message("You are unsubscribed. Reply START to re-subscribe.")
            return Response(content=str(resp), media_type="application/xml", status_code=200)
        if lower in {"start", "unstop"}:
            # fall through; also good place to flip a subscription flag back on
            pass
        if lower == "resend":
            # if you add Verify later, trigger resend here
            resp = MessagingResponse()
            resp.message("If you were verifying, we have resent your code.")
            return Response(content=str(resp), media_type="application/xml", status_code=200)

        existing_user_id = resolve_user_identifier_by_phone(e164)
        if existing_user_id is None:
            if lower in {"yes", "y", "start"}:
                user_id = get_or_create_user_for_phone(e164)
                bind_phone_to_user(e164, user_id)
                resp = MessagingResponse()
                resp.message("You are all set! You can now text me goals and updates any time.")
                return Response(content=str(resp), media_type="application/xml")
            else:
                resp = MessagingResponse()
                resp.message("Welcome! Reply YES to link this phone to a new account.")
                return Response(content=str(resp), media_type="application/xml")

        result = handle_incoming_message(
            message=body,
            phone_number=e164,
            to_number=to_number,
            sid=message_sid,
        )
        twiml = build_twilml_for_result(result)
        return Response(content=twiml, media_type="application/xml", status_code=200)

    except HTTPException as he:
        # On auth failures, 403 is fine; still return TwiML so logs are readable in Twilio
        resp = MessagingResponse()
        resp.message("Request could not be authenticated.")
        return Response(content=str(resp), media_type="application/xml", status_code=he.status_code)
    except Exception as e:
        # Never leak a 500 to Twilio; log server-side, reply friendly
        log.exception("Unhandled error in /webhook/sms")
        resp = MessagingResponse()
        resp.message("We hit a snag processing your message. Please try again.")
        return Response(content=str(resp), media_type="application/xml", status_code=200)

@router.post("/create_user")
def create_user(user: UserDoc):
    from app.services.firebase_service import add_new_user
    return add_new_user(user)
