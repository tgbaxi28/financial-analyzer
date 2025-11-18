"""Application configuration settings."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Application
    APP_NAME: str = "Financial Analyzer"
    APP_VERSION: str = "1.0.0"
    APP_URL: str = Field(default="http://localhost:8000")
    DEBUG: bool = Field(default=False)

    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    MAGIC_LINK_EXPIRE_MINUTES: int = 15

    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection URL")

    # Qdrant
    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: int = Field(default=6333)
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_PREFIX: str = "financial_docs"

    # AWS SES
    AWS_REGION: str = Field(default="us-east-1")
    AWS_ACCESS_KEY_ID: str = Field(...)
    AWS_SECRET_ACCESS_KEY: str = Field(...)
    SES_SENDER_EMAIL: str = Field(...)

    # File Upload
    UPLOAD_DIR: Path = Field(default=Path("/tmp/financial_uploads"))
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = "pdf,xlsx,xls,csv,docx"

    # WrenAI
    WRENAI_HOST: str = Field(default="localhost")
    WRENAI_PORT: int = Field(default=3000)
    WRENAI_API_KEY: Optional[str] = None

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    # Chunking Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Presidio
    PRESIDIO_ANALYZER_SCORE_THRESHOLD: float = 0.5

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables (like Docker-specific ones)

    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def allowed_extensions_list(self) -> list[str]:
        """Get list of allowed file extensions."""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    @property
    def wrenai_url(self) -> str:
        """Get full WrenAI URL."""
        return f"http://{self.WRENAI_HOST}:{self.WRENAI_PORT}"

    def ensure_upload_dir(self):
        """Create upload directory if it doesn't exist."""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
settings.ensure_upload_dir()
