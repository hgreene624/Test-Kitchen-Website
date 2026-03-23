"""Video service for handling video recording uploads and management."""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from src.models import VideoRecording, Candidate, InterviewPrompt, TranscriptionStatus
from src.lib.storage import (
    upload_video,
    delete_file,
    get_file_url,
    FileValidationError,
)
from src.config.settings import settings


class VideoService:
    """Service for handling video recording operations."""

    def __init__(self, db: AsyncSession):
        """Initialize video service with database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def upload_candidate_video(
        self,
        candidate_id: str,
        prompt_id: str,
        file: UploadFile,
        duration_seconds: int,
    ) -> VideoRecording:
        """Upload a video recording for a candidate's interview response.

        If a recording for this prompt already exists, it will be replaced (re-record).

        Args:
            candidate_id: UUID of the candidate
            prompt_id: UUID of the interview prompt
            file: FastAPI UploadFile object
            duration_seconds: Duration of the video in seconds

        Returns:
            Created or updated VideoRecording object

        Raises:
            ValueError: If candidate or prompt not found, or duration exceeds limit
            FileValidationError: If file validation fails
        """
        # Verify candidate exists
        result = await self.db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        candidate = result.scalar_one_or_none()

        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        # Verify prompt exists and is active
        prompt_result = await self.db.execute(
            select(InterviewPrompt).where(InterviewPrompt.id == prompt_id)
        )
        prompt = prompt_result.scalar_one_or_none()

        if not prompt:
            raise ValueError(f"Interview prompt {prompt_id} not found")

        if not prompt.is_active:
            raise ValueError(f"Interview prompt {prompt_id} is not active")

        # Validate duration (max 5 minutes = 300 seconds)
        max_duration = settings.max_video_duration_seconds
        if duration_seconds > max_duration:
            raise ValueError(
                f"Video duration ({duration_seconds}s) exceeds maximum allowed ({max_duration}s)"
            )

        # Check if video recording already exists (re-record scenario)
        existing_recording_result = await self.db.execute(
            select(VideoRecording).where(
                VideoRecording.candidate_id == candidate_id,
                VideoRecording.prompt_id == prompt_id,
            )
        )
        existing_recording = existing_recording_result.scalar_one_or_none()

        # If exists, delete old file from storage and remove old record
        if existing_recording:
            await delete_file(existing_recording.s3_key)
            # Delete the old recording (cascade will delete transcript)
            await self.db.delete(existing_recording)
            await self.db.flush()

        # Upload new file to storage
        file_path, file_url = await upload_video(
            file=file,
            candidate_id=str(candidate_id),
            prompt_id=str(prompt_id),
        )

        # Get file size
        content = await file.read()
        file_size = len(content)
        await file.seek(0)

        # Create new video recording
        video_recording = VideoRecording(
            candidate_id=candidate_id,
            prompt_id=prompt_id,
            file_url=file_url,
            file_name=file.filename,
            file_size_bytes=file_size,
            duration_seconds=duration_seconds,
            mime_type=file.content_type,
            s3_bucket=settings.storage_bucket_name,
            s3_key=file_path,
            transcription_status=TranscriptionStatus.PENDING,
        )

        self.db.add(video_recording)
        await self.db.commit()
        await self.db.refresh(video_recording)

        return video_recording

    async def get_candidate_recordings(
        self,
        candidate_id: str,
    ) -> List[VideoRecording]:
        """Get all video recordings for a candidate.

        Args:
            candidate_id: UUID of the candidate

        Returns:
            List of VideoRecording objects
        """
        result = await self.db.execute(
            select(VideoRecording)
            .where(VideoRecording.candidate_id == candidate_id)
            .order_by(VideoRecording.created_at)
        )
        return list(result.scalars().all())

    async def get_recording_by_id(
        self,
        recording_id: str,
        candidate_id: Optional[str] = None,
    ) -> Optional[VideoRecording]:
        """Get a specific video recording by ID.

        Args:
            recording_id: UUID of the video recording
            candidate_id: Optional candidate UUID to verify ownership

        Returns:
            VideoRecording object if found, None otherwise
        """
        query = select(VideoRecording).where(VideoRecording.id == recording_id)

        if candidate_id:
            query = query.where(VideoRecording.candidate_id == candidate_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def delete_recording(
        self,
        recording_id: str,
        candidate_id: str,
    ) -> bool:
        """Delete a video recording and its file from storage.

        This allows candidates to re-record their responses.

        Args:
            recording_id: UUID of the video recording
            candidate_id: UUID of the candidate (for ownership verification)

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If candidate does not own the recording
        """
        recording = await self.get_recording_by_id(recording_id, candidate_id)

        if not recording:
            return False

        if str(recording.candidate_id) != str(candidate_id):
            raise ValueError("Candidate does not own this recording")

        # Delete file from storage
        await delete_file(recording.s3_key)

        # Delete from database (cascade will delete transcript)
        await self.db.delete(recording)
        await self.db.commit()

        return True

    async def get_recording_url(
        self,
        recording_id: str,
        expires_in: int = 3600,
    ) -> Optional[str]:
        """Get access URL for a video recording.

        Args:
            recording_id: UUID of the video recording
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Signed URL for video access, None if recording not found
        """
        recording = await self.get_recording_by_id(recording_id)

        if not recording:
            return None

        # For local storage, file_url is already accessible
        # For S3, generate signed URL
        if settings.storage_backend == "s3":
            return await get_file_url(recording.s3_key, expires_in)
        else:
            return recording.file_url

    async def update_transcription_status(
        self,
        recording_id: str,
        status: TranscriptionStatus,
        error: Optional[str] = None,
    ) -> Optional[VideoRecording]:
        """Update transcription status for a video recording.

        Args:
            recording_id: UUID of the video recording
            status: New transcription status
            error: Optional error message if transcription failed

        Returns:
            Updated VideoRecording object, None if not found
        """
        recording = await self.get_recording_by_id(recording_id)

        if not recording:
            return None

        recording.transcription_status = status

        if error:
            recording.transcription_error = error

        # Update timestamps based on status
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        if status == TranscriptionStatus.PROCESSING:
            recording.transcription_started_at = now
        elif status in (TranscriptionStatus.COMPLETED, TranscriptionStatus.FAILED):
            recording.transcription_completed_at = now

        await self.db.commit()
        await self.db.refresh(recording)

        return recording

    async def get_recordings_pending_transcription(
        self,
        limit: int = 10,
    ) -> List[VideoRecording]:
        """Get video recordings that are pending transcription.

        Args:
            limit: Maximum number of recordings to return

        Returns:
            List of VideoRecording objects with pending transcription
        """
        result = await self.db.execute(
            select(VideoRecording)
            .where(VideoRecording.transcription_status == TranscriptionStatus.PENDING)
            .order_by(VideoRecording.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def check_candidate_has_prompt_recording(
        self,
        candidate_id: str,
        prompt_id: str,
    ) -> bool:
        """Check if candidate has already recorded a response for a prompt.

        Args:
            candidate_id: UUID of the candidate
            prompt_id: UUID of the interview prompt

        Returns:
            True if recording exists, False otherwise
        """
        result = await self.db.execute(
            select(VideoRecording).where(
                VideoRecording.candidate_id == candidate_id,
                VideoRecording.prompt_id == prompt_id,
            )
        )
        recording = result.scalar_one_or_none()
        return recording is not None
