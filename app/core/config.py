import os
from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    llm_api_key: str = "test-key"
    llm_base_url: Optional[str] = None
    default_model: str = "gpt-4o"
    openweathermap_api_key: str = "test-weather-key"
    database_url: str = "postgresql://localhost:5432/chatbot_db"
    log_level: str = "INFO"
    active_tools: Optional[str] = None  # Comma-separated tool names (e.g., "city,weather")


def get_settings() -> Settings:
    return Settings()