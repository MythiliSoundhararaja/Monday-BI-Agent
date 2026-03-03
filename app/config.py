from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    MONDAY_API_KEY: str
    WORK_ORDERS_BOARD_ID: int
    DEALS_BOARD_ID: int
    GEMINI_API_KEY: str
    ENV: str = "development"
    PORT: int = 8000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache()
def get_settings():
    return Settings()
