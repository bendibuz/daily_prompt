from fastapi import FastAPI
from app.adapters.firebase_client import init_firebase
import uvicorn

app = FastAPI()
init_firebase()

if __name__== "__main__":
   uvicorn.run(app, host="127.0.0.1", port=8000)