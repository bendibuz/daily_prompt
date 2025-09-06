from dataclasses import asdict, dataclass
from app.models.models import User, UserMessage, Goal
from firebase_admin import firestore
from twilio.twiml.messaging_response import MessagingResponse