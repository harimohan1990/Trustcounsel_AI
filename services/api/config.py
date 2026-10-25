import os
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    LOG_LEVEL: str = "INFO"
    APP_NAME: str = "TrustCounsel AI"
    API_PORT: int = 8000
    WEB_PORT: int = 5173

    # Security
    JWT_SECRET_KEY: str = "trustcounsel_super_secret_local_dev_key_must_be_256_bits_minimum_in_production!"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/trustcounsel_dev.db"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage
    STORAGE_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 52428800  # 50MB

    # AI Configuration
    MODEL_PROVIDER: Literal["mock", "openai", "anthropic", "ollama"] = "mock"
    EMBEDDING_PROVIDER: Literal["mock", "openai", "huggingface"] = "mock"
    EMBEDDING_DIMENSION: int = 384

    # Hosted Providers (Optional)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    ENABLE_OPENTELEMETRY: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs("./data/evals", exist_ok=True)
