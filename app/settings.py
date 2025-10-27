import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    database_url: str=os.getenv("DATABASE_URL", "postgresql://stelios19:192126SM@localhost:5432/flashcard-assistant")

    secret_key: str=os.getenv("SECRET_KEY", "super-secret-key")
    algorithm: str="HS256"
    access_token_expire_minutes: int=30

    openai_api_key: str=os.getenv("OPENAI_API_KEY", "")


settings = Settings()
