from fastapi import FastAPI
from datetime import datetime
from contextlib import asynccontextmanager
from main import app
from jobs import send_message
from apscheduler.schedulers.background import BackgroundScheduler  # runs tasks in the background
from apscheduler.triggers.cron import CronTrigger  # allows us to specify a recurring time for execution


morning_trigger = CronTrigger(hour=9, minute=0)  # midnight every day
morning_message = ''''''

afternoon_trigger = CronTrigger(hour=17, minute=0)  # midnight every day
afternoon_message = ''''''

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
