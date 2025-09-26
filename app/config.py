# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # Tell pydantic-settings how to load .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    GOOGLE_APPLICATION_CREDENTIALS: str = None  # path to the json file
    TWILIO_AUTH_TOKEN: str = None
    TWILIO_ACCOUNT_SID: str = None
    TWILIO_VERIFY_SID: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None
    PORT: Optional[str] = None

    # Required vars (keep required if you want validation to fail when missing)
    TWILIO_NUMBER: str = Field(..., description="Twilio phone number")
    MY_PHONE_NUMBER: str = Field(..., description="My phone number")

settings = Settings()
