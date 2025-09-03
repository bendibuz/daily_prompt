import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
MY_PHONE = os.getenv("MY_PHONE_NUMBER")

def send_test_sms():
    client = Client(TWILIO_SID, TWILIO_AUTH)
    message = client.messages.create(
        to=MY_PHONE,
        from_=TWILIO_NUMBER,
        body="🚀 This is a test SMS from your productivity bot!"
    )
    print(f"Message sent! SID: {message.sid}")

if __name__ == "__main__":
    send_test_sms()
