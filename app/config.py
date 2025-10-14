# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # Loads .env locally; Railway/Heroku-style env vars still override this.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Firebase: prefer FIREBASE_CREDENTIALS (raw/base64 JSON).
    FIREBASE_CREDENTIALS: Optional[str] = None     # raw JSON or base64 (recommended)
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None  # file path OR raw/base64 JSON (legacy/optional)

    # Twilio / misc
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_VERIFY_SID: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None
    PORT: Optional[str] = None  # Railway provides PORT

    # Required vars (keep required if you want startup to fail when missing)
    TWILIO_NUMBER: str = Field(..., description="Twilio phone number")
    MY_PHONE_NUMBER: str = Field(..., description="My phone number")

settings = Settings()
