from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "AI Business Health Analyzer"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    SECRET_KEY: str = "insecure-dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str = "postgresql+psycopg2://bha_user:bha_password@localhost:5432/bha_db"

    FRONTEND_ORIGIN: str = "http://localhost:5173"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    UPLOAD_DIR: str = "uploads"
    REPORTS_DIR: str = "reports"
    MAX_UPLOAD_SIZE_MB: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
