import os
from datetime import datetime
from twilio.rest import Client
from oauth2client.service_account import ServiceAccountCredentials

# --- ENV Variables ---
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
MY_PHONE = os.getenv("MY_PHONE_NUMBER")

def send_sms(message):
    client = Client(TWILIO_SID, TWILIO_AUTH)
    client.messages.create(to=MY_PHONE, from_=TWILIO_NUMBER, body=message)

