"""Background worker for processing video transcription jobs."""

import asyncio
import logging
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.models import VideoRecording, TranscriptionStatus
from src.services.transcription_service import TranscriptionService
from src.config.settings import settings
from src.config.database import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TranscriptionWorker:
    """Worker for processing video transcription jobs in the background."""

    def __init__(
        self,
        poll_interval: int = 30,
        max_concurrent_jobs: int = 5,
    ):
        """Initialize transcription worker.

        Args:
            poll_interval: Seconds between checking for new pending transcriptions
            max_concurrent_jobs: Maximum number of concurrent transcription jobs
        """
        self.poll_interval = poll_interval
        self.max_concurrent_jobs = max_concurrent_jobs
        self.running = False
        self.active_jobs: dict[str, asyncio.Task] = {}

    async def start(self):
        """Start the transcription worker."""
        self.running = True
        logger.info("Transcription worker started")

        while self.running:
            try:
                await self.process_pending_transcriptions()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in transcription worker loop: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval)

    async def stop(self):
        """Stop the transcription worker gracefully."""
        self.running = False
        logger.info("Stopping transcription worker...")

        # Wait for active jobs to complete
        if self.active_jobs:
            logger.info(f"Waiting for {len(self.active_jobs)} active jobs to complete...")
            await asyncio.gather(*self.active_jobs.values(), return_exceptions=True)

        logger.info("Transcription worker stopped")

    async def process_pending_transcriptions(self):
        """Check for and process pending transcription jobs."""
        # Create database session
        async for db in get_db():
            try:
                from src.services.video_service import VideoService

                video_service = VideoService(db)

                # Get pending recordings
                pending_recordings = await video_service.get_recordings_pending_transcription(
                    limit=self.max_concurrent_jobs - len(self.active_jobs)
                )

                if not pending_recordings:
                    logger.debug("No pending transcriptions found")
                    return

                logger.info(f"Found {len(pending_recordings)} pending transcriptions")

                # Process each pending recording
                for recording in pending_recordings:
                    if len(self.active_jobs) >= self.max_concurrent_jobs:
                        logger.info(
                            f"Max concurrent jobs ({self.max_concurrent_jobs}) reached, waiting..."
                        )
                        break

                    # Start transcription job
                    job_id = str(recording.id)
                    if job_id not in self.active_jobs:
                        task = asyncio.create_task(
                            self.process_transcription(str(recording.id))
                        )
                        self.active_jobs[job_id] = task
                        logger.info(
                            f"Started transcription job for recording {recording.id}"
                        )

                # Clean up completed jobs
                completed_jobs = [
                    job_id
                    for job_id, task in self.active_jobs.items()
                    if task.done()
                ]
                for job_id in completed_jobs:
                    del self.active_jobs[job_id]
                    logger.debug(f"Removed completed job {job_id}")

            except Exception as e:
                logger.error(f"Error processing pending transcriptions: {e}", exc_info=True)
            finally:
                break

    async def process_transcription(self, video_recording_id: str):
        """Process a single transcription job.

        Args:
            video_recording_id: UUID of the video recording
        """
        logger.info(f"Processing transcription for recording {video_recording_id}")

        async for db in get_db():
            try:
                transcription_service = TranscriptionService(db)

                # Trigger transcription job
                assemblyai_job_id = await transcription_service.trigger_transcription(
                    video_recording_id
                )

                if not assemblyai_job_id:
                    logger.error(
                        f"Failed to trigger transcription for recording {video_recording_id}"
                    )
                    return

                logger.info(
                    f"Triggered AssemblyAI job {assemblyai_job_id} for recording {video_recording_id}"
                )

                # Poll for completion
                result = await transcription_service.poll_transcription_status(
                    job_id=assemblyai_job_id,
                    max_retries=settings.transcription_retry_max_attempts,
                    retry_interval=10,  # Poll every 10 seconds
                )

                if result.get("status") == "completed":
                    # Save transcription result
                    transcript = await transcription_service.save_transcription_result(
                        video_recording_id=video_recording_id,
                        transcription_data=result,
                    )

                    if transcript:
                        logger.info(
                            f"Successfully saved transcript for recording {video_recording_id}"
                        )
                    else:
                        logger.error(
                            f"Failed to save transcript for recording {video_recording_id}"
                        )
                else:
                    # Transcription failed
                    error = result.get("error", "Unknown error")
                    logger.error(
                        f"Transcription failed for recording {video_recording_id}: {error}"
                    )

                    # Update recording status
                    from src.services.video_service import VideoService

                    video_service = VideoService(db)
                    await video_service.update_transcription_status(
                        recording_id=video_recording_id,
                        status=TranscriptionStatus.FAILED,
                        error=error,
                    )

            except Exception as e:
                logger.error(
                    f"Error processing transcription for recording {video_recording_id}: {e}",
                    exc_info=True,
                )

                # Mark as failed
                try:
                    from src.services.video_service import VideoService

                    video_service = VideoService(db)
                    await video_service.update_transcription_status(
                        recording_id=video_recording_id,
                        status=TranscriptionStatus.FAILED,
                        error=str(e),
                    )
                except Exception as update_error:
                    logger.error(
                        f"Failed to update transcription status: {update_error}",
                        exc_info=True,
                    )
            finally:
                break


async def run_worker():
    """Run the transcription worker (entry point for standalone execution)."""
    worker = TranscriptionWorker(
        poll_interval=30,  # Check every 30 seconds
        max_concurrent_jobs=3,  # Process up to 3 transcriptions concurrently
    )

    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        await worker.stop()


if __name__ == "__main__":
    """Run the worker as a standalone process."""
    asyncio.run(run_worker())
