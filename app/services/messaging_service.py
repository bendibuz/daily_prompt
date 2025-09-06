from dataclasses import asdict, dataclass
from app.models.models import User, UserMessage, Goal
from firebase_admin import firestore
from twilio.twiml.messaging_response import MessagingResponse
from app.adapters.firebase_client import get_firebase_client

get_firebase_client()
db = firestore.client()

def parse_response(response: UserMessage):
        goal_list = [response.split(";")]
        return goal_list
        
def save_user_response(reponse: UserMessage):
    db.collection("user_responses").add(asdict(reponse))

def get_user_goals(user: User):
    db.collection("goals")
    
def save_user_goals(response: UserMessage):
    parsed_res = parse_response(response)
    for goal in parsed_res:
        db.collection("goals").add(asdict(goal))



    