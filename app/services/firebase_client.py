import os
import firebase_admin
from firebase_admin import credentials

def init_firebase():
    cred = credentials.Certificate(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    app = firebase_admin.initialize_app(cred)
    return app