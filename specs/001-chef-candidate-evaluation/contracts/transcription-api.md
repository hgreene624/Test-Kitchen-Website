# Async Transcription Processing API Contract

**Service**: Asynchronous Video Transcription
**Technology**: FastAPI with background task queue (Celery/RQ) + third-party transcription API
**Base URL**: `/api/v1/transcriptions`

---

## Overview

Video transcription is processed asynchronously to avoid blocking candidate submission flow. The system follows a job-based pattern:

1. **Trigger**: Transcription job created automatically after video upload finalization
2. **Processing**: Background worker sends video to third-party API (AWS Transcribe, AssemblyAI, etc.)
3. **Polling**: Client polls job status to check progress
4. **Completion**: Transcript available for download, labeled with prompt + candidate name

**Graceful Degradation**: If transcription fails or service is unavailable, candidate can still complete submission. Admin sees "transcription unavailable" status and can review video directly.

---

## Endpoints

### POST /transcriptions/trigger

**Purpose**: Manually trigger transcription job for a video recording (typically called automatically after video upload)

**Auth Required**: Yes | Role: candidate (own videos) or admin

**Request**:
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: application/json`
- **Body**:
  ```json
  {
    "recording_id": "string - UUID of video recording (required)",
    "language_code": "string - ISO language code (optional, default 'en-US')",
    "priority": "string - 'normal' or 'high' (optional, default 'normal', admin only)"
  }
  ```

**Response**:
- **Success (201 Created)**:
  ```json
  {
    "job_id": "string - UUID of transcription job",
    "recording_id": "string - UUID",
    "status": "string - 'pending'",
    "language_code": "string - 'en-US'",
    "priority": "string - 'normal' or 'high'",
    "created_at": "string - ISO 8601 timestamp",
    "estimated_completion_time": "string - ISO 8601 timestamp (current time + ~10 minutes)",
    "message": "Transcription job created. Check status at /transcriptions/{job_id}/status"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Transcription already in progress for this recording",
    "code": "TRANSCRIPTION_IN_PROGRESS",
    "details": {
      "existing_job_id": "string - UUID",
      "status": "processing"
    }
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Transcription already completed for this recording",
    "code": "TRANSCRIPTION_ALREADY_COMPLETED",
    "details": {
      "transcript_id": "string - UUID",
      "completed_at": "string - ISO 8601 timestamp"
    }
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Unsupported language code",
    "code": "UNSUPPORTED_LANGUAGE",
    "details": {
      "requested_language": "fr-FR",
      "supported_languages": ["en-US", "en-GB", "es-ES"]
    }
  }
  ```
- **Error (401 Unauthorized)**:
  ```json
  {
    "error": "Invalid or expired token",
    "code": "INVALID_TOKEN"
  }
  ```
- **Error (403 Forbidden)**:
  ```json
  {
    "error": "You can only request transcription for your own recordings",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Video recording not found",
    "code": "RECORDING_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to create transcription job",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only trigger transcription for their own videos
- Admins can trigger transcription for any video
- Only one active transcription job allowed per recording (prevents duplicates)
- If transcription already completed, returns 400 with existing transcript info
- Default language: en-US (English - United States)
- Priority parameter only available to admins (normal vs high queue)
- Job queued in background task system (Celery/RQ)
- Estimated completion time: ~10 minutes for 5-minute video (varies by service load)

**Referenced FRs**: FR-005, FR-006, FR-018, FR-021

---

### GET /transcriptions/{job_id}/status

**Purpose**: Check status of transcription job (poll for completion)

**Auth Required**: Yes | Role: candidate (own jobs) or admin

**Request**:
- **Path Parameters**:
  - `job_id`: string (UUID) - ID of transcription job
- **Headers**:
  - `Authorization: Bearer {jwt_token}`

**Response**:
- **Success (200 OK)** (pending):
  ```json
  {
    "job_id": "string - UUID",
    "recording_id": "string - UUID",
    "status": "string - 'pending'",
    "created_at": "string - ISO 8601 timestamp",
    "estimated_completion_time": "string - ISO 8601 timestamp",
    "message": "Transcription job is queued. Please check again in a few moments."
  }
  ```
- **Success (200 OK)** (processing):
  ```json
  {
    "job_id": "string - UUID",
    "recording_id": "string - UUID",
    "status": "string - 'processing'",
    "created_at": "string - ISO 8601 timestamp",
    "started_at": "string - ISO 8601 timestamp",
    "progress_percentage": "number - 0-100 (if available from service)",
    "estimated_completion_time": "string - ISO 8601 timestamp",
    "message": "Transcription in progress. Please check again shortly."
  }
  ```
- **Success (200 OK)** (completed):
  ```json
  {
    "job_id": "string - UUID",
    "recording_id": "string - UUID",
    "status": "string - 'completed'",
    "created_at": "string - ISO 8601 timestamp",
    "started_at": "string - ISO 8601 timestamp",
    "completed_at": "string - ISO 8601 timestamp",
    "transcript_id": "string - UUID",
    "transcript_url": "string - URL to fetch transcript (use /transcriptions/{job_id}/result)",
    "confidence_score": "number - 0.0 to 1.0 (average confidence)",
    "duration_seconds": "number - video duration",
    "message": "Transcription completed successfully"
  }
  ```
- **Success (200 OK)** (failed):
  ```json
  {
    "job_id": "string - UUID",
    "recording_id": "string - UUID",
    "status": "string - 'failed'",
    "created_at": "string - ISO 8601 timestamp",
    "started_at": "string - ISO 8601 timestamp",
    "failed_at": "string - ISO 8601 timestamp",
    "error_message": "string - description of failure",
    "error_code": "string - error code from transcription service",
    "is_retryable": "boolean - whether job can be retried",
    "message": "Transcription failed. Video remains accessible for manual review."
  }
  ```
- **Success (200 OK)** (unavailable):
  ```json
  {
    "job_id": "string - UUID",
    "recording_id": "string - UUID",
    "status": "string - 'unavailable'",
    "created_at": "string - ISO 8601 timestamp",
    "error_message": "string - 'Transcription service unavailable'",
    "is_retryable": "boolean - true",
    "message": "Transcription service is currently unavailable. Video remains accessible for manual review."
  }
  ```
- **Error (401 Unauthorized)**:
  ```json
  {
    "error": "Invalid or expired token",
    "code": "INVALID_TOKEN"
  }
  ```
- **Error (403 Forbidden)**:
  ```json
  {
    "error": "You can only check status of your own transcription jobs",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Transcription job not found",
    "code": "JOB_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to retrieve job status",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only check status of their own jobs
- Admins can check status of any job
- Status values: pending, processing, completed, failed, unavailable
- Polling interval recommendation: 10-15 seconds during active transcription
- Progress percentage may not be available (depends on third-party API)
- Failed jobs include error details for debugging
- Graceful degradation: failed/unavailable status allows candidate to proceed without transcript
- Job records retained for 90 days for audit purposes

**Referenced FRs**: FR-005, FR-006, FR-021, FR-022

---

### GET /transcriptions/{job_id}/result

**Purpose**: Retrieve completed transcript with metadata and download URL

**Auth Required**: Yes | Role: candidate (own transcripts) or admin

**Request**:
- **Path Parameters**:
  - `job_id`: string (UUID) - ID of transcription job
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
- **Query Parameters**:
  - `format`: string - "json" or "txt" (default: "json")

**Response**:
- **Success (200 OK)** (format=json):
  ```json
  {
    "transcript_id": "string - UUID",
    "job_id": "string - UUID",
    "recording_id": "string - UUID",
    "candidate_id": "string - UUID",
    "candidate_name": "string",
    "prompt_id": "string - UUID",
    "prompt_text": "string - interview question",
    "text": "string - full transcript text",
    "confidence_score": "number - 0.0 to 1.0 (average)",
    "language_code": "string - 'en-US'",
    "duration_seconds": "number",
    "word_count": "number",
    "file_name": "string - formatted as '[Prompt Text] - [Candidate Name].txt'",
    "file_url": "string - signed URL for downloadable .txt file (1 hour expiry)",
    "created_at": "string - ISO 8601 timestamp",
    "words": [
      {
        "word": "string",
        "start_time": "number - seconds from start",
        "end_time": "number - seconds from start",
        "confidence": "number - 0.0 to 1.0"
      }
    ]
  }
  ```
- **Success (200 OK)** (format=txt):
  ```
  Content-Type: text/plain
  Content-Disposition: attachment; filename="[Prompt Text] - [Candidate Name].txt"

  [Full transcript text without timestamps]
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Transcription not yet completed",
    "code": "TRANSCRIPTION_NOT_READY",
    "details": {
      "current_status": "processing",
      "message": "Check /transcriptions/{job_id}/status for completion"
    }
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Transcription failed or unavailable",
    "code": "TRANSCRIPTION_FAILED",
    "details": {
      "status": "failed",
      "error_message": "Audio quality too low for transcription"
    }
  }
  ```
- **Error (401 Unauthorized)**:
  ```json
  {
    "error": "Invalid or expired token",
    "code": "INVALID_TOKEN"
  }
  ```
- **Error (403 Forbidden)**:
  ```json
  {
    "error": "You can only access your own transcripts",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Transcription job not found",
    "code": "JOB_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to retrieve transcript",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only access their own transcripts
- Admins can access any transcript
- Only available when job status is "completed"
- Filename formatted as: "[Prompt Text] - [Candidate Name].txt"
- format=json includes word-level timing and confidence data
- format=txt returns plain text file for download
- Confidence score averaged across all words
- Low confidence scores (<0.7) should be flagged for manual review
- Transcript stored with encryption at rest

**Referenced FRs**: FR-005, FR-006, FR-019, FR-020, FR-038

---

### POST /transcriptions/{job_id}/retry

**Purpose**: Retry failed or unavailable transcription job

**Auth Required**: Yes | Role: candidate (own jobs) or admin

**Request**:
- **Path Parameters**:
  - `job_id`: string (UUID) - ID of failed transcription job
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: application/json`
- **Body**: None (empty)

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "job_id": "string - UUID (same job ID, status reset)",
    "recording_id": "string - UUID",
    "status": "string - 'pending'",
    "retry_count": "number - incremented",
    "created_at": "string - ISO 8601 timestamp (original)",
    "retried_at": "string - ISO 8601 timestamp (now)",
    "message": "Transcription job retried. Check status for progress."
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Job is not in a retryable state",
    "code": "NOT_RETRYABLE",
    "details": {
      "current_status": "completed",
      "message": "Only failed or unavailable jobs can be retried"
    }
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Maximum retry attempts exceeded",
    "code": "MAX_RETRIES_EXCEEDED",
    "details": {
      "retry_count": 3,
      "max_retries": 3,
      "message": "Job has been retried maximum number of times"
    }
  }
  ```
- **Error (401 Unauthorized)**:
  ```json
  {
    "error": "Invalid or expired token",
    "code": "INVALID_TOKEN"
  }
  ```
- **Error (403 Forbidden)**:
  ```json
  {
    "error": "You can only retry your own transcription jobs",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Transcription job not found",
    "code": "JOB_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to retry transcription job",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only retry their own jobs
- Admins can retry any job
- Only failed or unavailable jobs can be retried
- Maximum 3 retry attempts per job
- Retry resets job status to "pending" and re-queues
- retry_count incremented on each retry
- Original job_id preserved (no new job created)
- Retry logged to audit trail

**Referenced FRs**: FR-005, FR-006, FR-022

---

### GET /transcriptions/by-candidate/{candidate_id}

**Purpose**: Retrieve all transcription jobs for a specific candidate

**Auth Required**: Yes | Role: candidate (own jobs) or admin

**Request**:
- **Path Parameters**:
  - `candidate_id`: string (UUID) - ID of the candidate
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
- **Query Parameters**:
  - `status`: string - filter by status: "pending", "processing", "completed", "failed", "unavailable" (optional, comma-separated)
  - `include_transcript`: boolean - include full transcript text in response (default: false)

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "candidate_id": "string - UUID",
    "jobs": [
      {
        "job_id": "string - UUID",
        "recording_id": "string - UUID",
        "prompt_id": "string - UUID",
        "prompt_text": "string",
        "sequence_order": "number",
        "status": "string - 'pending', 'processing', 'completed', 'failed', 'unavailable'",
        "created_at": "string - ISO 8601 timestamp",
        "completed_at": "string - ISO 8601 timestamp (null if not completed)",
        "transcript": {
          "transcript_id": "string - UUID",
          "text": "string - only if include_transcript=true and status=completed",
          "confidence_score": "number - 0.0 to 1.0",
          "file_name": "string",
          "file_url": "string - signed URL"
        }
      }
    ],
    "total_jobs": "number",
    "status_counts": {
      "pending": "number",
      "processing": "number",
      "completed": "number",
      "failed": "number",
      "unavailable": "number"
    }
  }
  ```
- **Error (401 Unauthorized)**:
  ```json
  {
    "error": "Invalid or expired token",
    "code": "INVALID_TOKEN"
  }
  ```
- **Error (403 Forbidden)**:
  ```json
  {
    "error": "You can only view your own transcription jobs",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Candidate not found",
    "code": "CANDIDATE_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to retrieve transcription jobs",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only view their own jobs
- Admins can view any candidate's jobs
- Jobs ordered by sequence_order (matching prompt order)
- Status filter supports multiple values (e.g., "failed,unavailable")
- include_transcript=false for faster loading (excludes full text)
- status_counts provides quick summary for UI display
- Returns empty array if no transcription jobs exist

**Referenced FRs**: FR-005, FR-006, FR-021, FR-037

---

## Webhooks (Optional)

### POST /transcriptions/webhook/callback

**Purpose**: Receive completion notification from third-party transcription service

**Auth Required**: No (validated via signature verification)

**Request**:
- **Headers**:
  - `X-Signature`: string - HMAC signature for request validation
  - `Content-Type: application/json`
- **Body** (example from AssemblyAI):
  ```json
  {
    "job_id": "string - internal job ID",
    "external_id": "string - third-party service job ID",
    "status": "string - 'completed' or 'failed'",
    "transcript": "string - full transcript text (if completed)",
    "confidence": "number - 0.0 to 1.0",
    "words": [
      {
        "word": "string",
        "start": "number - milliseconds",
        "end": "number - milliseconds",
        "confidence": "number"
      }
    ],
    "error": "string - error message (if failed)"
  }
  ```

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "message": "Webhook received and processed"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Invalid signature",
    "code": "INVALID_SIGNATURE"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Job not found",
    "code": "JOB_NOT_FOUND"
  }
  ```

**Business Rules**:
- Signature verified using shared secret from transcription service
- Updates job status and saves transcript to database
- Generates formatted transcript file (.txt) and uploads to storage
- Triggers notification to candidate (optional)
- Idempotent: duplicate webhooks handled gracefully

**Referenced FRs**: FR-018, FR-019, FR-021

---

## Transcription Service Integration

**Supported Services**:
- AWS Transcribe
- Google Speech-to-Text
- AssemblyAI
- Deepgram
- Whisper (self-hosted)

**Configuration** (environment variables):
```
TRANSCRIPTION_SERVICE=assemblyai
TRANSCRIPTION_API_KEY=your_api_key
TRANSCRIPTION_LANGUAGE=en-US
TRANSCRIPTION_WEBHOOK_URL=https://yourapp.com/api/v1/transcriptions/webhook/callback
TRANSCRIPTION_MAX_RETRIES=3
```

---

## Common Error Responses

**401 Unauthorized**:
```json
{
  "error": "Authentication required",
  "code": "AUTHENTICATION_REQUIRED"
}
```

**429 Too Many Requests**:
```json
{
  "error": "Too many transcription requests. Please try again later.",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": "number - seconds"
}
```

**503 Service Unavailable**:
```json
{
  "error": "Transcription service temporarily unavailable",
  "code": "SERVICE_UNAVAILABLE",
  "message": "Video uploaded successfully. Transcription will be attempted later."
}
```

---

## Pydantic Schema Examples

**TriggerTranscriptionRequest**:
```python
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class Priority(str, Enum):
    NORMAL = "normal"
    HIGH = "high"

class TriggerTranscriptionRequest(BaseModel):
    recording_id: str
    language_code: str = Field(default="en-US")
    priority: Priority = Field(default=Priority.NORMAL)
```

**TranscriptionStatusResponse**:
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class TranscriptionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"

class TranscriptionStatusResponse(BaseModel):
    job_id: str
    recording_id: str
    status: TranscriptionStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    estimated_completion_time: Optional[datetime] = None
    progress_percentage: Optional[float] = None
    transcript_id: Optional[str] = None
    transcript_url: Optional[str] = None
    confidence_score: Optional[float] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    is_retryable: Optional[bool] = None
    message: str
```

**TranscriptWord**:
```python
from pydantic import BaseModel

class TranscriptWord(BaseModel):
    word: str
    start_time: float  # seconds
    end_time: float  # seconds
    confidence: float  # 0.0 to 1.0
```

**TranscriptResultResponse**:
```python
from pydantic import BaseModel
from typing import List
from datetime import datetime

class TranscriptResultResponse(BaseModel):
    transcript_id: str
    job_id: str
    recording_id: str
    candidate_id: str
    candidate_name: str
    prompt_id: str
    prompt_text: str
    text: str
    confidence_score: float
    language_code: str
    duration_seconds: int
    word_count: int
    file_name: str
    file_url: str
    created_at: datetime
    words: List[TranscriptWord]
```
