from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import app.routes.routes as routes
import os
from app.services.utilities.serial_service import SerialServiceAsync
from app.services.utilities.serial_noop import NoopSerialService
from contextlib import asynccontextmanager

MODE = (os.getenv("USE_SERIAL", "auto") or "auto").lower()  # "auto" | "true" | "false"

async def make_serial_service():
    if MODE == "false":
        print("🚫 Serial disabled by config")
        return NoopSerialService()

    svc = SerialServiceAsync()  # COM3 inside implementation, or pass port if needed
    try:
        await svc.open()
        svc.available = True
        print("🔌 Serial connected")
        return svc
    except Exception as e:
        if MODE == "true":
            # hard fail only if explicitly required
            raise
        print(f"⚠️ Serial unavailable, using Noop ({e})")
        return NoopSerialService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.svc = await make_serial_service()
    # optional: wire button callback even for Noop (it will safely ignore)
    def log_button_sync(pressed: bool):
        print(f"[BTN] {'👇 PRESSED' if pressed else '🫳 RELEASED'}")
    app.state.svc.on_button(log_button_sync)

    try:
        yield
    finally:
        await app.state.svc.close()

app = FastAPI(lifespan=lifespan)

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