from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import app.routes.routes as routes
import os
from app.services.utilities.serial_service import SerialServiceAsync
from contextlib import asynccontextmanager

# USE_SERIAL = False
USE_SERIAL = True

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if USE_SERIAL:
        print("🔌 Using serial service")
        await svc.open()
        svc.on_button(log_button) 
        app.state.svc = svc
        try:
            yield
        finally:
            # Shutdown
            await svc.close()
    else:
        print("🚫 Not using serial service")

async def log_button(pressed: bool):
    if USE_SERIAL:
        print(f"[BTN] {'👇 PRESSED' if pressed else '🫳 RELEASED'}")
        await svc.blink_led(1)

app = FastAPI(lifespan=lifespan)
if USE_SERIAL:
    svc = SerialServiceAsync()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ "http://localhost:5173", "http://localhost:3000" ],
    allow_credentials=True,
    allow_methods=["*"],   # <- includes OPTIONS
    allow_headers=["*"],
)




app.include_router(routes.router)


if __name__== "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)