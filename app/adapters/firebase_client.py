# adapters/firebase_client.py
import firebase_admin
from firebase_admin import credentials
from app.config import settings

def init_firebase():
    # If GOOGLE_APPLICATION_CREDENTIALS is a path to your JSON file:
    cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
    app = firebase_admin.initialize_app(cred)
    return app

firebase_client = init_firebase()

def get_firebase_client():
    return firebase_client
