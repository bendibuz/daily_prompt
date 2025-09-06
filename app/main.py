from fastapi import FastAPI
from app.adapters.firebase_client import init_firebase


app = FastAPI()
init_firebase()

