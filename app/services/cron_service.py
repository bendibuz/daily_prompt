# app/services/cron_service.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
import logging

from firebase_admin import firestore
from twilio.rest import Client

from app.adapters.firebase_client import get_firebase_client
from app.config import settings
from app.models.models import UserDoc
from app.services.firebase_service import get_today_goals_for_user, dicts_to_goals

log = logging.getLogger("cron_service")

# Initialize Firebase
get_firebase_client()
db = firestore.client()

# Initialize Twilio client
def _get_twilio_client() -> Client:
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        raise RuntimeError("Missing Twilio credentials")
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

twilio_client = _get_twilio_client()

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


def send_sms(to_number: str, message: str):
    """Send SMS via Twilio"""
    try:
        twilio_client.messages.create(
            to=to_number,
            from_=settings.TWILIO_NUMBER,
            body=message
        )
        log.info(f"Sent SMS to {to_number}")
    except Exception as e:
        log.error(f"Failed to send SMS to {to_number}: {e}")


def build_morning_message() -> str:
    """Build the morning prompt message"""
    return """Good morning! 🌞

What are your top goals for today?

You can include points with your goals to set priorities:
- "Walk the dog 5"
- "Go to the gym 10"
- "Finish project 3"

Send multiple goals on separate lines."""


def build_evening_message(user: UserDoc) -> str:
    """Build the evening check-in message with current goal status"""
    try:
        today_goals = get_today_goals_for_user(user)

        if not today_goals:
            pass
        goals_list = []
        for goal in today_goals:
            status = "✓" if goal.complete else "▢"
            goals_list.append(f"{status} {goal.goal_text} ({goal.points} pt)")

        goals_text = "\n".join(goals_list)

        total_points = sum(g.points for g in today_goals)
        completed_points = sum(g.points for g in today_goals if g.complete)

        return f"""Good evening! 🌆

Here's your progress today:

{goals_text}

Progress: {completed_points}/{total_points} pts

Reply with "done <goal name>" to mark any incomplete goals as done!
(Replace <goal name> with the exact text of your goal.)"""

    except Exception as e:
        log.error(f"Error building evening message for user {user.user_id}: {e}")
        return """Good evening! 🌆

How did your day go? Text me any updates!"""


def get_active_users():
    """Get all users who have notifications enabled (activated = True)"""
    try:
        users_ref = db.collection("users").where("activated", "==", True)
        docs = users_ref.stream()

        users = []
        for doc in docs:
            data = doc.to_dict() or {}
            user = UserDoc(
                user_id=data.get("user_id", doc.id),
                display_name=data.get("display_name"),
                email=data.get("email"),
                timezone=data.get("timezone", "America/Chicago"),
                phones=data.get("phones", []),
                activated=data.get("activated", False),
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at"),
            )
            users.append(user)

        return users
    except Exception as e:
        log.error(f"Error fetching active users: {e}")
        return []


def morning_job():
    """Send morning prompts to all active users"""
    log.info("Running morning job")

    users = get_active_users()
    message = build_morning_message()

    for user in users:
        if not user.phones:
            log.warning(f"User {user.user_id} has no phone numbers")
            continue

        # Send to primary phone (first in list)
        primary_phone = user.phones[0]
        send_sms(primary_phone, message)

    log.info(f"Morning job completed - sent to {len(users)} users")


def evening_job():
    """Send evening check-in to all active users"""
    log.info("Running evening job")

    users = get_active_users()

    for user in users:
        if not user.phones:
            log.warning(f"User {user.user_id} has no phone numbers")
            continue

        message = build_evening_message(user)

        # Send to primary phone (first in list)
        primary_phone = user.phones[0]
        send_sms(primary_phone, message)

    log.info(f"Evening job completed - sent to {len(users)} users")


def start_scheduler():
    """Start the APScheduler with morning and evening jobs"""
    global scheduler

    if scheduler is not None:
        log.warning("Scheduler already running")
        return

    scheduler = AsyncIOScheduler()

    # Morning prompt at 9:00 AM (in server timezone)
    # Note: For user-specific timezones, you'd need per-user jobs
    morning_trigger = CronTrigger(hour=9, minute=0)
    scheduler.add_job(morning_job, morning_trigger, id="morning_prompt")

    # Evening prompt at 6:00 PM (in server timezone)
    evening_trigger = CronTrigger(hour=18, minute=0)
    scheduler.add_job(evening_job, evening_trigger, id="evening_prompt")

    scheduler.start()
    log.info("Scheduler started with morning (9:00 AM) and evening (6:00 PM) jobs")


def stop_scheduler():
    """Stop the scheduler gracefully"""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        log.info("Scheduler stopped")
