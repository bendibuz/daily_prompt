
from main import app
from services.incoming import save_user_response
from app.models.models import User, UserMessage, Goal
from app.services.firebase_service import create_user_v2

@app.post("/user_response/")
def handle_response(response: UserMessage):
    try:
        save_user_response(response)
    except Exception as e:
        raise(e)

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


# @app.route("/reply_sms")
# def receive_message():
#     resp = MessagingResponse()
#     resp.message("The Robots are coming! Head for the hills!")

#     # Return the TwiML (as XML) response
#     return Response(str(resp), mimetype='text/xml')

@app.post("/create_user")
def create_user(user: User):
    create_user_v2(user)