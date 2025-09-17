from fastapi import FastAPI
from datetime import datetime
from contextlib import asynccontextmanager
from main import app
from jobs import send_message
from models import Goal
from typing import List
from apscheduler.schedulers.background import BackgroundScheduler  # runs tasks in the background
from apscheduler.triggers.cron import CronTrigger  # allows us to specify a recurring time for execution

# def get_goal_statuses():
    

def build_afternoon_message(goals: List[Goal]):
    goals_list = []
    for goal in goals:
        goal_status =  "Complete" if goal.complete else "Incomplete"
        goals_list.append(f"{goal.goal_text}: {goal_status} ({goal.points})")
    goals_message = "\n".join(goals_list)
    message = f"Hello! Checking in on your goals status. Send me any updates! \n {goals_message}"
    return message
#TODO: 


morning_trigger = CronTrigger(hour=9, minute=0)  # midnight every day

afternoon_trigger = CronTrigger(hour=17, minute=0)  # midnight every day
morning_message = '''
                    Good morning!
                    What are your top goals for today?
                    You can include a score with your goal to set a priority for yourself.
                    Separate goals with a semicolon and the score with a comma.
                    Example:
                    Walk the dog, 5;
                    Go to the gym, 10;
                    '''

afternoon_message = build_afternoon_message(goals)


# The task to run
def morning_task():
    print(f"Task is running at {datetime.now()}")
    send_message(morning_message)
    # ... additional task code goes here ...
def afternoon_task():
    print(f"Task is running at {datetime.now()}")
    send_message(afternoon_message)
    # ... additional task code goes here ...

# Set up the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(morning_task, morning_trigger)
scheduler.add_job(afternoon_task, afternoon_trigger)
scheduler.start()

# Ensure the scheduler shuts down properly on application exit.
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    scheduler.shutdown()

@app.get("/")
def read_root():
    return {"message": "FastAPI with APScheduler Demo"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
