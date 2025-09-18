import os
import firebase_admin
from firebase_admin import credentials
from app.config import settings
import json

def init_firebase():
    cred = credentials.Certificate(json.loads(os.environ["TEST_VAR"]))
    app = firebase_admin.initialize_app(cred)
    return app

firebase_client = init_firebase()

def get_firebase_client():
    return firebase_client