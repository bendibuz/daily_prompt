from fastapi import FastAPI
from app.adapters.firebase_client import init_firebase
import uvicorn
import app.routes.routes as routes

# init_firebase()
app = FastAPI()
app.include_router(routes.router)


if __name__== "__main__":
   uvicorn.run(app, host="127.0.0.1", port=8000)