from fastapi import FastAPI
from firebase_client import init_firebase


app = FastAPI()
init_firebase()

