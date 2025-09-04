from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_FROM_NUMBER: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()
