from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None
    TWILIO_NUMBER: str = Field(..., description="Twilio phone number")
    MY_PHONE_NUMBER: str = Field(..., description="My phone number")

    class Config:
        env_file = ".env"

settings = Settings()
