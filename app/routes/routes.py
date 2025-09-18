from app.services.messaging_service import save_user_response
from app.models.models import User, UserMessage, Goal
from twilio.twiml.messaging_response import MessagingResponse
from fastapi import APIRouter, Request
from app.main import app

router = APIRouter()


from app.services.firebase_service import create_user_v2

@app.get("/")
def root_response():
    return("Hello World!")

@app.post("/webhook/sms")
async def receive_sms(request: Request):
    form_data = await request.form()
    phone_number = form_data.get("From")
    message_body = form_data.get("Body")
    # handle_incoming_message(message_body)
    print(f"Message from {phone_number}: {message_body}")
    
    return {"status": "received"}

# Add goals for the day
@app.post("/daily-goals/")
def create_daily_goals(goals: list[Goal]):
    for goal in goals:
        try:
            return {"message" : "Goal posted"}
        except Exception as e:
            raise(e)
        
# Check the status of today's goals for prompt to user midday
@app.get("/status/")
def check_status():
    return {"goal statuses"}


# Update status based on user feedback
@app.put("/status/")
def update_status():
    pass


@app.route("/reply_sms")
def receive_message():
    resp = MessagingResponse()
    resp.message("The Robots are coming! Head for the hills!")

    return str(resp)

@app.post("/create_user")
def create_user(user: User):
    create_user_v2(user)
