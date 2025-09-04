from dataclasses import asdict, dataclass
from app.models.models import User, UserMessage, Goal
from firebase_admin import firestore
from main import app

db = firestore.client()

@app.post("/user_responses/")
def save_user_response(reponse: UserMessage):
    db.collection("user_responses").add(asdict(reponse))

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