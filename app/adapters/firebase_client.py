# firebase_client.py
import firebase_admin
from firebase_admin import credentials
from app.config import settings

def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
        return firebase_admin.initialize_app(cred)
    return firebase_admin.get_app()

firebase_client = init_firebase()

def get_firebase_client():
    return firebase_client
