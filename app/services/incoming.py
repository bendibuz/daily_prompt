from dataclasses import asdict, dataclass
from app.models.models import User, UserMessage, Goal
from firebase_admin import firestore
from twilio.twiml.messaging_response import MessagingResponse
db = firestore.client()

def save_user_response(reponse: UserMessage):
    db.collection("user_responses").add(asdict(reponse))

def get_user_goals(user: User):
    db.collection("goals")
    