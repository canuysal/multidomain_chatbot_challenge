import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = "test-key"
    openweathermap_api_key: str = "test-weather-key"
    database_url: str = "postgresql://localhost:5432/chatbot_db"

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()