import os
import firebase_admin
from firebase_admin import credentials
from app.config import settings

def init_firebase():
    cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
    app = firebase_admin.initialize_app(cred)
    return app