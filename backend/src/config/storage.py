"""Storage client configuration supporting local filesystem and S3-compatible storage."""
import os
from pathlib import Path
from typing import Optional, BinaryIO
from abc import ABC, abstractmethod

from .settings import settings


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def save_file(
        self, file_data: BinaryIO, file_path: str, content_type: Optional[str] = None
    ) -> str:
        """Save file and return public URL."""
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> None:
        """Delete file from storage."""
        pass

    @abstractmethod
    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Get public or signed URL for file access."""
        pass

    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        pass


class LocalFilesystemStorage(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, base_path: str, base_url: str):
        """
        Initialize local filesystem storage.

        Args:
            base_path: Absolute path to storage directory (e.g., /var/www/chef-candidate-media)
            base_url: Public URL prefix for serving files (e.g., https://yourdomain.com/media)
        """
        self.base_path = Path(base_path)
        self.base_url = base_url.rstrip("/")

        # Create storage directories if they don't exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create storage directory structure."""
        subdirs = ["videos", "documents", "photos", "transcripts"]
        for subdir in subdirs:
            (self.base_path / subdir).mkdir(parents=True, exist_ok=True)

    def _get_absolute_path(self, file_path: str) -> Path:
        """
        Get absolute filesystem path from relative file path.

        Args:
            file_path: Relative path (e.g., videos/candidate_id/video.mp4)

        Returns:
            Absolute Path object
        """
        # Normalize path and prevent directory traversal attacks
        clean_path = os.path.normpath(file_path).lstrip("/").lstrip("\\")
        return self.base_path / clean_path

    async def save_file(
        self, file_data: BinaryIO, file_path: str, content_type: Optional[str] = None
    ) -> str:
        """
        Save file to local filesystem.

        Args:
            file_data: File binary data
            file_path: Relative path (e.g., videos/candidate_id/video.mp4)
            content_type: MIME type (unused for local storage)

        Returns:
            Public URL for accessing the file
        """
        abs_path = self._get_absolute_path(file_path)

        # Create parent directories if needed
        abs_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file to disk
        with open(abs_path, "wb") as f:
            if hasattr(file_data, "read"):
                # File-like object
                f.write(file_data.read())
            else:
                # Bytes
                f.write(file_data)

        # Return public URL
        return f"{self.base_url}/{file_path}"

    async def delete_file(self, file_path: str) -> None:
        """Delete file from local filesystem."""
        abs_path = self._get_absolute_path(file_path)
        if abs_path.exists():
            abs_path.unlink()

    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        Get public URL for file (no expiration for local filesystem).

        Args:
            file_path: Relative path (e.g., videos/candidate_id/video.mp4)
            expires_in: Unused for local storage (no signed URLs)

        Returns:
            Public URL
        """
        return f"{self.base_url}/{file_path}"

    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists on local filesystem."""
        abs_path = self._get_absolute_path(file_path)
        return abs_path.exists() and abs_path.is_file()


class S3Storage(StorageBackend):
    """S3-compatible storage backend (AWS S3, MinIO, Backblaze B2, etc.)."""

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region: str = "us-east-1",
        endpoint_url: Optional[str] = None,
    ):
        """
        Initialize S3 storage.

        Args:
            access_key: AWS access key ID
            secret_key: AWS secret access key
            bucket_name: S3 bucket name
            region: AWS region
            endpoint_url: Custom endpoint (for MinIO, Backblaze, etc.)
        """
        try:
            import boto3
            from botocore.client import Config
        except ImportError:
            raise RuntimeError(
                "boto3 is required for S3 storage. Install with: pip install boto3"
            )

        client_config = Config(
            region_name=region,
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        )

        self._client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
            config=client_config,
        )
        self.bucket_name = bucket_name

    async def save_file(
        self, file_data: BinaryIO, file_path: str, content_type: Optional[str] = None
    ) -> str:
        """Save file to S3."""
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        if hasattr(file_data, "read"):
            data = file_data.read()
        else:
            data = file_data

        self._client.put_object(
            Bucket=self.bucket_name, Key=file_path, Body=data, **extra_args
        )

        return f"https://{self.bucket_name}.s3.amazonaws.com/{file_path}"

    async def delete_file(self, file_path: str) -> None:
        """Delete file from S3."""
        self._client.delete_object(Bucket=self.bucket_name, Key=file_path)

    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Get signed URL for S3 file access."""
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": file_path},
            ExpiresIn=expires_in,
        )

    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in S3."""
        try:
            self._client.head_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except Exception:
            return False


# Initialize storage backend based on settings
def get_storage_backend() -> StorageBackend:
    """
    Get configured storage backend.

    Returns:
        StorageBackend instance based on settings.storage_type
    """
    if settings.storage_type == "local":
        return LocalFilesystemStorage(
            base_path=settings.storage_base_path, base_url=settings.storage_base_url
        )
    elif settings.storage_type in ("s3", "minio"):
        if not settings.aws_access_key_id or not settings.aws_secret_access_key:
            raise ValueError(
                "AWS credentials required for S3 storage. "
                "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables."
            )
        return S3Storage(
            access_key=settings.aws_access_key_id,
            secret_key=settings.aws_secret_access_key,
            bucket_name=settings.s3_bucket_name,
            region=settings.aws_region,
            endpoint_url=settings.s3_endpoint_url,
        )
    else:
        raise ValueError(
            f"Unknown storage type: {settings.storage_type}. "
            f"Supported types: local, s3, minio"
        )


# Global storage client instance
storage = get_storage_backend()
