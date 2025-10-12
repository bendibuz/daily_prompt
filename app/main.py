from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import app.routes.routes as routes
import os
from app.services.utilities.button_read import listen

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ "http://localhost:5173", "http://localhost:3000" ],
    allow_credentials=True,
    allow_methods=["*"],   # <- includes OPTIONS
    allow_headers=["*"],
)


app.include_router(routes.router)

listen()

if __name__== "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)