from app.models.models import UserDoc
from twilio.twiml.messaging_response import MessagingResponse
from fastapi import APIRouter, Request, Response, HTTPException
from app.services.messaging_service import (
    handle_incoming_message, 
    # build_twilml_for_result,
)
from app.services.auth_phone import get_or_create_user_for_phone, bind_phone_to_user
from app.utilities import normalize_to_e164
import os
from twilio.request_validator import RequestValidator
import logging
from app.config import settings
import asyncio

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

@router.post("/webhook/sms")
async def receive_sms(request: Request):
    try:
        asyncio.create_task(request.app.state.svc.blink_led(2))
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

        result = handle_incoming_message(
            message=body,
            phone_number=e164,
            to_number=to_number,
            sid=message_sid,
        )
        print(f'🚀 Result: {result}')
        # twiml = build_twilml_for_result(result)
        return Response(content=str(result), media_type="application/xml", status_code=200)
        # return str(result)

    except HTTPException as he:
        resp = MessagingResponse()
        resp.message("Request could not be authenticated.")
        return Response(content=str(resp), media_type="application/xml", status_code=he.status_code)
    except Exception as e:
        log.exception("Unhandled error in /webhook/sms")
        resp = MessagingResponse()
        resp.message("😵‍💫 Something went wrong...")
        return Response(content=str(resp), media_type="application/xml", status_code=200)

@router.post("/testpath")
async def test_receive_sms(request: Request, body: str = ""):
    try:
        asyncio.create_task(request.app.state.svc.blink_led(2))
        # form = await validate_twilio_request(request)
        raw_from = "+18478587030"
        body = body.strip()
        to_number = "Tester"
        message_sid = "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

        try:
            e164 = normalize_to_e164(raw_from)
        except Exception:
            resp = MessagingResponse()
            resp.message("We could not read your phone number. Please try again.")
            log.warning("Bad From: %r sid=%r", raw_from, message_sid)
            return Response(content=str(resp), media_type="application/xml", status_code=200)

        result = handle_incoming_message(
            message=body,
            phone_number=e164,
            to_number=to_number,
            sid=message_sid,
        )
        print(f'🚀 Result: {result}')
        # twiml = build_twilml_for_result(result)
        return Response(content=str(result), media_type="application/xml", status_code=200)
        # return str(result)

    except HTTPException as he:
        resp = MessagingResponse()
        resp.message("Request could not be authenticated.")
        return Response(content=str(resp), media_type="application/xml", status_code=he.status_code)
    except Exception as e:
        log.exception("Unhandled error in /webhook/sms")
        resp = MessagingResponse()
        resp.message("😵‍💫 Something went wrong...")
        return Response(content=str(resp), media_type="application/xml", status_code=200)

@router.post("/create_user")
def create_user(user: UserDoc):
    from app.services.firebase_service import add_new_user
    return add_new_user(user)

