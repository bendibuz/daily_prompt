from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_FROM_NUMBER: str | None = None
    TWILIO_NUMBER: Field(..., description="Twilio phone number")
    MY_PHONE_NUMBER: Field(..., description="My phone number")

    class Config:
        env_file = ".env"

settings = Settings()
