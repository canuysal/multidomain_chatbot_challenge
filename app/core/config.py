import os
from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = "test-key"
    openweathermap_api_key: str = "test-weather-key"
    database_url: str = "postgresql://localhost:5432/chatbot_db"
    log_level: str = "INFO"
    default_model: str = "gpt-4o"


def get_settings() -> Settings:
    return Settings()