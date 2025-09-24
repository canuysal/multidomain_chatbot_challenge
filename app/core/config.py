import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = "test-key"
    openweathermap_api_key: str = "test-weather-key"
    database_url: str = "postgresql://localhost:5432/chatbot_db"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields in .env file


def get_settings() -> Settings:
    return Settings()