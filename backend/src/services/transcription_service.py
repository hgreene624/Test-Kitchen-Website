"""Transcription service for AssemblyAI API integration."""

import asyncio
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import VideoRecording, Transcript, TranscriptionStatus, Candidate, InterviewPrompt
from src.lib.storage import save_transcript
from src.config.settings import settings


class TranscriptionService:
    """Service for handling video transcription with AssemblyAI."""

    ASSEMBLYAI_API_URL = "https://api.assemblyai.com/v2"

    def __init__(self, db: AsyncSession):
        """Initialize transcription service with database session.

        Args:
            db: Async database session
        """
        self.db = db
        self.api_key = settings.assemblyai_api_key

    async def trigger_transcription(
        self,
        video_recording_id: str,
    ) -> Optional[str]:
        """Trigger transcription job for a video recording.

        Args:
            video_recording_id: UUID of the video recording

        Returns:
            AssemblyAI job ID if successful, None if failed

        Raises:
            ValueError: If video recording not found
        """
        # Get video recording
        result = await self.db.execute(
            select(VideoRecording).where(VideoRecording.id == video_recording_id)
        )
        recording = result.scalar_one_or_none()

        if not recording:
            raise ValueError(f"Video recording {video_recording_id} not found")

        # Update status to processing
        recording.transcription_status = TranscriptionStatus.PROCESSING
        recording.transcription_started_at = datetime.now(timezone.utc)
        await self.db.commit()

        try:
            # Submit transcription job to AssemblyAI
            job_id = await self._submit_transcription_job(recording.file_url)

            if job_id:
                return job_id
            else:
                # Failed to submit job
                recording.transcription_status = TranscriptionStatus.FAILED
                recording.transcription_error = "Failed to submit transcription job to AssemblyAI"
                recording.transcription_completed_at = datetime.now(timezone.utc)
                await self.db.commit()
                return None

        except Exception as e:
            # Graceful degradation - mark as unavailable instead of failed
            recording.transcription_status = TranscriptionStatus.UNAVAILABLE
            recording.transcription_error = f"AssemblyAI service unavailable: {str(e)}"
            recording.transcription_completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            return None

    async def _submit_transcription_job(self, audio_url: str) -> Optional[str]:
        """Submit transcription job to AssemblyAI.

        Args:
            audio_url: URL of the video/audio file

        Returns:
            Job ID if successful, None otherwise
        """
        headers = {
            "authorization": self.api_key,
            "content-type": "application/json",
        }

        payload = {
            "audio_url": audio_url,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.ASSEMBLYAI_API_URL}/transcript",
                json=payload,
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("id")
            else:
                return None

    async def check_transcription_status(
        self,
        job_id: str,
    ) -> Dict[str, Any]:
        """Check status of an AssemblyAI transcription job.

        Args:
            job_id: AssemblyAI job ID

        Returns:
            Dictionary with status information:
            {
                "status": str (queued, processing, completed, error),
                "text": Optional[str],
                "confidence": Optional[float],
                "error": Optional[str]
            }
        """
        headers = {
            "authorization": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.ASSEMBLYAI_API_URL}/transcript/{job_id}",
                    headers=headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": data.get("status"),
                        "text": data.get("text"),
                        "confidence": data.get("confidence"),
                        "error": data.get("error"),
                        "words": data.get("words"),
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"API request failed with status {response.status_code}",
                    }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to check transcription status: {str(e)}",
            }

    async def poll_transcription_status(
        self,
        job_id: str,
        max_retries: int = None,
        retry_interval: int = 5,
    ) -> Dict[str, Any]:
        """Poll AssemblyAI for transcription completion.

        Args:
            job_id: AssemblyAI job ID
            max_retries: Maximum number of retries (default from settings)
            retry_interval: Interval between retries in seconds

        Returns:
            Final transcription result
        """
        if max_retries is None:
            max_retries = settings.transcription_retry_max_attempts

        for attempt in range(max_retries):
            result = await self.check_transcription_status(job_id)
            status = result.get("status")

            if status == "completed":
                return result
            elif status == "error":
                return result
            elif status in ("queued", "processing"):
                # Still processing, wait and retry
                await asyncio.sleep(retry_interval)
            else:
                # Unknown status
                return {
                    "status": "error",
                    "error": f"Unknown transcription status: {status}",
                }

        # Max retries exceeded
        return {
            "status": "error",
            "error": f"Transcription polling exceeded maximum retries ({max_retries})",
        }

    async def get_transcription_result(
        self,
        job_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get completed transcription result.

        Args:
            job_id: AssemblyAI job ID

        Returns:
            Transcription data if completed, None otherwise
        """
        result = await self.check_transcription_status(job_id)

        if result.get("status") == "completed":
            return result
        else:
            return None

    async def save_transcription_result(
        self,
        video_recording_id: str,
        transcription_data: Dict[str, Any],
    ) -> Optional[Transcript]:
        """Save transcription result to database and storage.

        Args:
            video_recording_id: UUID of the video recording
            transcription_data: Transcription data from AssemblyAI

        Returns:
            Created Transcript object, None if failed
        """
        # Get video recording with relationships
        result = await self.db.execute(
            select(VideoRecording)
            .where(VideoRecording.id == video_recording_id)
        )
        recording = result.scalar_one_or_none()

        if not recording:
            return None

        # Get candidate and prompt for filename formatting
        candidate_result = await self.db.execute(
            select(Candidate).where(Candidate.id == recording.candidate_id)
        )
        candidate = candidate_result.scalar_one_or_none()

        prompt_result = await self.db.execute(
            select(InterviewPrompt).where(InterviewPrompt.id == recording.prompt_id)
        )
        prompt = prompt_result.scalar_one_or_none()

        if not candidate or not prompt:
            return None

        # Extract transcription data
        transcript_text = transcription_data.get("text", "")
        confidence_score = transcription_data.get("confidence", 0.0)
        words = transcription_data.get("words", [])
        word_count = len(words) if words else len(transcript_text.split())

        # Save transcript file to storage
        file_path, file_url = await save_transcript(
            transcript_text=transcript_text,
            candidate_id=str(candidate.id),
            prompt_text=prompt.prompt_text[:50],  # Truncate prompt for filename
            candidate_name=candidate.full_name or candidate.email,
        )

        # Create transcript record
        transcript = Transcript(
            video_recording_id=video_recording_id,
            transcript_text=transcript_text,
            confidence_score=confidence_score,
            word_count=word_count,
            file_url=file_url,
            file_name=f"{prompt.prompt_text[:50]} - {candidate.full_name or candidate.email}.txt",
            s3_bucket=settings.storage_bucket_name,
            s3_key=file_path,
            provider="assemblyai",
            provider_metadata={
                "words": words,
                "audio_duration": transcription_data.get("audio_duration"),
            },
        )

        self.db.add(transcript)

        # Update video recording status
        recording.transcription_status = TranscriptionStatus.COMPLETED
        recording.transcription_completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(transcript)

        return transcript

    async def handle_transcription_webhook(
        self,
        webhook_data: Dict[str, Any],
    ) -> bool:
        """Handle webhook callback from AssemblyAI.

        Args:
            webhook_data: Webhook payload from AssemblyAI

        Returns:
            True if processed successfully, False otherwise
        """
        job_id = webhook_data.get("transcript_id")
        status = webhook_data.get("status")

        if not job_id:
            return False

        # Find video recording by checking transcription_status = PROCESSING
        # In production, you'd want to store job_id in VideoRecording
        # For MVP, we'll poll instead of using webhooks

        # TODO: Implement webhook handling when job_id tracking is added
        return True

    async def retry_failed_transcription(
        self,
        video_recording_id: str,
    ) -> Optional[str]:
        """Retry transcription for a failed recording.

        Args:
            video_recording_id: UUID of the video recording

        Returns:
            New job ID if successful, None otherwise
        """
        result = await self.db.execute(
            select(VideoRecording).where(VideoRecording.id == video_recording_id)
        )
        recording = result.scalar_one_or_none()

        if not recording:
            return None

        # Only retry if status is FAILED or UNAVAILABLE
        if recording.transcription_status not in (
            TranscriptionStatus.FAILED,
            TranscriptionStatus.UNAVAILABLE,
        ):
            return None

        # Reset status and trigger new transcription
        recording.transcription_status = TranscriptionStatus.PENDING
        recording.transcription_error = None
        await self.db.commit()

        return await self.trigger_transcription(video_recording_id)
