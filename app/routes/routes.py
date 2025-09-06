from app.services.messaging_service import save_user_response
from app.models.models import User, UserMessage, Goal
from twilio.twiml.messaging_response import MessagingResponse
from fastapi import APIRouter

router = APIRouter()


from app.services.firebase_service import create_user_v2

@router.post("/user_response/")
def handle_response(response: UserMessage):
    try:
        save_user_response(response)
    except Exception as e:
        raise(e)

# Add goals for the day
@router.post("/daily-goals/")
def create_daily_goals(goals: list[Goal]):
    for goal in goals:
        try:
            return {"message" : "Goal posted"}
        except Exception as e:
            raise(e)
        
# Check the status of today's goals for prompt to user midday
@router.get("/status/")
def check_status():
    return {"goal statuses"}


# Update status based on user feedback
@router.put("/status/")
def update_status():
    pass


# @router.route("/reply_sms")
# def receive_message():
#     resp = MessagingResponse()
#     resp.message("The Robots are coming! Head for the hills!")

#     return str(resp)

@router.post("/create_user")
def create_user(user: User):
    create_user_v2(user)
