"""Application settings loaded from environment variables."""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable loading."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/chef_candidates"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"

    # AWS S3 Configuration
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "chef-candidate-media"
    s3_endpoint_url: Optional[str] = None  # For MinIO/local development

    # AssemblyAI Configuration
    assemblyai_api_key: str

    # JWT Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_hours: int = 24

    # Email Verification
    email_verification_token_expire_hours: int = 48

    # Application Settings
    app_name: str = "Chef Candidate Evaluation Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # File Upload Limits (in MB, converted to bytes)
    max_video_size_mb: int = 100
    max_document_size_mb: int = 10
    max_photo_size_mb: int = 5

    @property
    def max_video_size_bytes(self) -> int:
        """Get max video size in bytes."""
        return self.max_video_size_mb * 1024 * 1024

    @property
    def max_document_size_bytes(self) -> int:
        """Get max document size in bytes."""
        return self.max_document_size_mb * 1024 * 1024

    @property
    def max_photo_size_bytes(self) -> int:
        """Get max photo size in bytes."""
        return self.max_photo_size_mb * 1024 * 1024

    # Video Recording Limits
    max_video_duration_seconds: int = 300

    # Data Retention
    data_retention_days: int = 90

    # Transcription Settings
    transcription_retry_max_attempts: int = 3
    transcription_timeout_minutes: int = 10


# Global settings instance
settings = Settings()
