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

# --- SMS Prompt ---
def send_sms():
    message = (
        "Good morning, Ben 🌞 What are your top 3 tasks for today?\n"
        "Reply with each one and a point value (1–5).\n"
        "Example:\n1. Finish deck (5)\n2. Email supplier (2)\n3. Dev Sunny nav (4)"
    )
    client = Client(TWILIO_SID, TWILIO_AUTH)
    client.messages.create(to=MY_PHONE, from_=TWILIO_NUMBER, body=message)

# --- Main ---
if __name__ == "__main__":
    send_sms()
