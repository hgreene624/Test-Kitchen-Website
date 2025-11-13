"""S3 storage client configuration using boto3."""
import boto3
from botocore.client import Config
from typing import Optional

from .settings import settings


class S3Client:
    """S3 client wrapper for file operations."""

    def __init__(self) -> None:
        """Initialize S3 client with configuration from settings."""
        # Configure S3 client
        client_config = Config(
            region_name=settings.aws_region,
            signature_version='s3v4',
            s3={'addressing_style': 'path'},  # Required for MinIO compatibility
        )

        # Create S3 client (supports both AWS S3 and MinIO)
        self._client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            endpoint_url=settings.s3_endpoint_url,  # None for AWS, URL for MinIO
            config=client_config,
        )

        self.bucket_name = settings.s3_bucket_name

    @property
    def client(self):
        """Get underlying boto3 S3 client."""
        return self._client

    def get_bucket(self) -> str:
        """Get configured bucket name."""
        return self.bucket_name

    async def ensure_bucket_exists(self) -> None:
        """
        Ensure S3 bucket exists, create if it doesn't.

        Useful for development with MinIO.
        """
        try:
            self._client.head_bucket(Bucket=self.bucket_name)
        except Exception:
            # Bucket doesn't exist, create it
            try:
                if settings.s3_endpoint_url:
                    # MinIO or custom endpoint
                    self._client.create_bucket(Bucket=self.bucket_name)
                else:
                    # AWS S3
                    if settings.aws_region == 'us-east-1':
                        self._client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self._client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={
                                'LocationConstraint': settings.aws_region
                            }
                        )
            except Exception as e:
                raise RuntimeError(f"Failed to create S3 bucket: {e}")


# Global S3 client instance
s3_client = S3Client()
