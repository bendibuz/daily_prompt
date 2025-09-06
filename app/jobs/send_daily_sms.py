import os
import pytz
from datetime import datetime
from twilio.rest import Client
from oauth2client.service_account import ServiceAccountCredentials

# --- ENV Variables ---
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
MY_PHONE = os.getenv("MY_PHONE_NUMBER")

morning_message = '''Good morning, Ben 🌞!
        What are your most important goals for the day?
        List a goal and a score separated by a comma
        Separate goals with a semicolon, like this:
        Water the plants, 5;
        Wash the dishes, 10
        '''

def build_string(goals):
    msg_string = ", ".join(goal for goal in goals)
    return msg_string

afternoon_checkin = (
    f'Just checking in... have you completed... {goal.name for goal in goals}'
)


# --- SMS Prompt ---
def send_sms():
    
    client = Client(TWILIO_SID, TWILIO_AUTH)
    client.messages.create(to=MY_PHONE, from_=TWILIO_NUMBER, body=message)

# --- Main ---
if __name__ == "__main__":
    send_sms(morning_message)
