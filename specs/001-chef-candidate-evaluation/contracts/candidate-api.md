# Candidate Submission API Contract

**Service**: Candidate Submission Workflows
**Technology**: FastAPI with Pydantic schemas, multipart file uploads
**Base URL**: `/api/v1/candidates`

---

## Endpoints

### POST /candidates/{candidate_id}/documents

**Purpose**: Upload resume or cover letter document for candidate profile

**Auth Required**: Yes | Role: candidate

**Request**:
- **Path Parameters**:
  - `candidate_id`: string (UUID) - ID of the candidate
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: multipart/form-data`
- **Body** (multipart/form-data):
  ```
  document_type: string - "resume" or "cover_letter" (required)
  file: binary - document file (required)
  ```

**Response**:
- **Success (201 Created)**:
  ```json
  {
    "id": "string - UUID of document record",
    "candidate_id": "string - UUID",
    "document_type": "string - 'resume' or 'cover_letter'",
    "file_name": "string - original filename",
    "file_size": "number - bytes",
    "file_url": "string - signed URL for download (temporary, 1 hour expiry)",
    "uploaded_at": "string - ISO 8601 timestamp",
    "message": "Document uploaded successfully"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Invalid file format. Supported formats: PDF, DOC, DOCX",
    "code": "INVALID_FILE_FORMAT"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "File size exceeds maximum limit of 10 MB",
    "code": "FILE_TOO_LARGE",
    "details": {
      "max_size_mb": 10,
      "uploaded_size_mb": 15.2
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
    "error": "You can only upload documents to your own account",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to upload document",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only upload documents to their own account (candidate_id must match JWT token)
- Supported formats: PDF, DOC, DOCX
- Maximum file size: 10 MB
- Document type must be "resume" or "cover_letter"
- If document type already exists, previous upload is replaced (versioning optional)
- Files stored with encryption at rest
- Signed URL expires after 1 hour

**Referenced FRs**: FR-005, FR-007, FR-008, FR-010

---

### GET /candidates/{candidate_id}/documents

**Purpose**: Retrieve list of uploaded documents for candidate

**Auth Required**: Yes | Role: candidate (own data) or admin

**Request**:
- **Path Parameters**:
  - `candidate_id`: string (UUID) - ID of the candidate
- **Headers**:
  - `Authorization: Bearer {jwt_token}`

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "candidate_id": "string - UUID",
    "documents": [
      {
        "id": "string - UUID",
        "document_type": "string - 'resume' or 'cover_letter'",
        "file_name": "string",
        "file_size": "number - bytes",
        "file_url": "string - signed URL (1 hour expiry)",
        "uploaded_at": "string - ISO 8601 timestamp"
      }
    ]
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
    "error": "You can only view your own documents",
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
    "error": "Failed to retrieve documents",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only view their own documents
- Admins can view any candidate's documents
- Returns empty array if no documents uploaded
- Signed URLs regenerated on each request

**Referenced FRs**: FR-005, FR-009

---

### PUT /candidates/{candidate_id}/documents/{document_id}

**Purpose**: Replace existing document with new upload

**Auth Required**: Yes | Role: candidate

**Request**:
- **Path Parameters**:
  - `candidate_id`: string (UUID) - ID of the candidate
  - `document_id`: string (UUID) - ID of the document to replace
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: multipart/form-data`
- **Body** (multipart/form-data):
  ```
  file: binary - new document file (required)
  ```

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "id": "string - UUID (same document_id)",
    "candidate_id": "string - UUID",
    "document_type": "string - 'resume' or 'cover_letter'",
    "file_name": "string - new filename",
    "file_size": "number - bytes",
    "file_url": "string - signed URL",
    "uploaded_at": "string - ISO 8601 timestamp (updated)",
    "message": "Document updated successfully"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Invalid file format. Supported formats: PDF, DOC, DOCX",
    "code": "INVALID_FILE_FORMAT"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Cannot update document after final submission",
    "code": "SUBMISSION_FINALIZED"
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
    "error": "You can only update your own documents",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Document not found",
    "code": "DOCUMENT_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to update document",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only update their own documents
- Same file format and size validations as upload
- Cannot update after candidate has submitted final application
- Previous file is deleted from storage
- Timestamp is updated to reflect new upload time

**Referenced FRs**: FR-005, FR-009, FR-054

---

### GET /prompts

**Purpose**: Retrieve all active interview prompts for candidate video wizard

**Auth Required**: Yes | Role: candidate

**Request**:
- **Headers**:
  - `Authorization: Bearer {jwt_token}`

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "prompts": [
      {
        "id": "string - UUID",
        "prompt_text": "string - interview question",
        "sequence_order": "number - display order (1-based)",
        "time_limit_seconds": "number - optional max recording time (null if no limit, default 300)",
        "created_at": "string - ISO 8601 timestamp"
      }
    ],
    "total_prompts": "number - count of prompts"
  }
  ```
- **Error (401 Unauthorized)**:
  ```json
  {
    "error": "Invalid or expired token",
    "code": "INVALID_TOKEN"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to retrieve prompts",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Returns only active prompts (inactive/deleted prompts excluded)
- Prompts ordered by sequence_order ascending
- Once candidate starts interview, prompt set is frozen (candidates see original prompts even if admin changes them)
- Default time limit is 300 seconds (5 minutes)

**Referenced FRs**: FR-011, FR-014, FR-051

---

### POST /candidates/{candidate_id}/recordings

**Purpose**: Submit video recording for an interview prompt

**Auth Required**: Yes | Role: candidate

**Request**:
- **Path Parameters**:
  - `candidate_id`: string (UUID) - ID of the candidate
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: multipart/form-data`
- **Body** (multipart/form-data):
  ```
  prompt_id: string (UUID) - ID of the interview prompt (required)
  video: binary - video file (required)
  duration_seconds: number - video duration in seconds (required)
  ```

**Response**:
- **Success (201 Created)**:
  ```json
  {
    "id": "string - UUID of recording",
    "candidate_id": "string - UUID",
    "prompt_id": "string - UUID",
    "file_url": "string - signed URL for playback",
    "duration_seconds": "number",
    "upload_timestamp": "string - ISO 8601 timestamp",
    "transcription_status": "string - 'pending'",
    "transcription_job_id": "string - UUID of async transcription job",
    "message": "Video uploaded successfully. Transcription will begin shortly."
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Video duration exceeds maximum limit of 5 minutes",
    "code": "VIDEO_TOO_LONG",
    "details": {
      "max_duration_seconds": 300,
      "uploaded_duration_seconds": 420
    }
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Invalid video format. Supported formats: WebM, MP4",
    "code": "INVALID_VIDEO_FORMAT"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Recording for this prompt already exists. Use PUT to replace.",
    "code": "DUPLICATE_RECORDING"
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
    "error": "You can only upload recordings to your own account",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Interview prompt not found",
    "code": "PROMPT_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to upload video",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only upload to their own account
- Supported formats: WebM, MP4 (H.264 codec)
- Maximum duration: 5 minutes (300 seconds)
- Maximum file size: ~100 MB (derived from 5 min video)
- One recording per prompt per candidate (use PUT to re-record)
- Transcription job starts automatically after upload
- File stored with encryption at rest

**Referenced FRs**: FR-005, FR-012, FR-013, FR-015, FR-018

---

### GET /candidates/{candidate_id}/recordings

**Purpose**: Retrieve all video recordings for candidate

**Auth Required**: Yes | Role: candidate (own data) or admin

**Request**:
- **Path Parameters**:
  - `candidate_id`: string (UUID) - ID of the candidate
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
- **Query Parameters**:
  - `include_transcript`: boolean - include transcript data if available (default: false)

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "candidate_id": "string - UUID",
    "recordings": [
      {
        "id": "string - UUID",
        "prompt_id": "string - UUID",
        "prompt_text": "string - interview question",
        "sequence_order": "number - prompt order",
        "file_url": "string - signed URL for playback (1 hour expiry)",
        "duration_seconds": "number",
        "upload_timestamp": "string - ISO 8601 timestamp",
        "transcription_status": "string - 'pending', 'processing', 'completed', 'failed', 'unavailable'",
        "transcription_job_id": "string - UUID (null if failed)",
        "transcript": {
          "id": "string - UUID",
          "text": "string - transcribed text (only if include_transcript=true and status=completed)",
          "confidence_score": "number - 0.0 to 1.0",
          "file_url": "string - signed URL for downloadable .txt file",
          "generated_at": "string - ISO 8601 timestamp"
        }
      }
    ],
    "total_recordings": "number",
    "expected_recordings": "number - total active prompts"
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
    "error": "You can only view your own recordings",
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
    "error": "Failed to retrieve recordings",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only view their own recordings
- Admins can view any candidate's recordings
- Returns empty array if no recordings
- Signed URLs regenerated on each request
- Transcript field only populated if include_transcript=true and transcription completed
- expected_recordings shows how many prompts candidate should answer

**Referenced FRs**: FR-005, FR-016, FR-021, FR-037

---

### PUT /candidates/{candidate_id}/recordings/{recording_id}

**Purpose**: Re-record video response for an interview prompt

**Auth Required**: Yes | Role: candidate

**Request**:
- **Path Parameters**:
  - `candidate_id`: string (UUID) - ID of the candidate
  - `recording_id`: string (UUID) - ID of the recording to replace
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: multipart/form-data`
- **Body** (multipart/form-data):
  ```
  video: binary - new video file (required)
  duration_seconds: number - video duration in seconds (required)
  ```

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "id": "string - UUID (same recording_id)",
    "candidate_id": "string - UUID",
    "prompt_id": "string - UUID",
    "file_url": "string - signed URL for new video",
    "duration_seconds": "number",
    "upload_timestamp": "string - ISO 8601 timestamp (updated)",
    "transcription_status": "string - 'pending' (restarted)",
    "transcription_job_id": "string - UUID of new transcription job",
    "message": "Video re-recorded successfully. New transcription started."
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Cannot re-record after final submission",
    "code": "SUBMISSION_FINALIZED"
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
    "error": "You can only update your own recordings",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Recording not found",
    "code": "RECORDING_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to update recording",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only update their own recordings
- Same validations as POST (format, duration, size)
- Cannot update after final submission
- Previous video file deleted from storage
- Previous transcription invalidated, new transcription job started
- Timestamp updated to reflect re-recording time

**Referenced FRs**: FR-005, FR-013, FR-016, FR-054

---

### GET /menus/{menu_id}/dishes

**Purpose**: Retrieve menu with all dishes organized by category for candidate review

**Auth Required**: Yes | Role: candidate

**Request**:
- **Path Parameters**:
  - `menu_id`: string (UUID) - ID of the menu (typically single active menu)
- **Headers**:
  - `Authorization: Bearer {jwt_token}`

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "menu_id": "string - UUID",
    "menu_name": "string",
    "menu_description": "string",
    "categories": [
      {
        "id": "string - UUID",
        "category_name": "string - e.g., 'Appetizers', 'Mains', 'Desserts'",
        "sequence_order": "number",
        "dishes": [
          {
            "id": "string - UUID",
            "dish_name": "string",
            "description": "string",
            "photo_urls": ["string - signed URLs for dish photos"],
            "active": "boolean"
          }
        ]
      }
    ],
    "total_dishes": "number"
  }
  ```
- **Error (401 Unauthorized)**:
  ```json
  {
    "error": "Invalid or expired token",
    "code": "INVALID_TOKEN"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Menu not found",
    "code": "MENU_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to retrieve menu",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Returns only active dishes
- Categories ordered by sequence_order
- Dishes ordered by creation date within each category
- Photo URLs are signed and expire after 1 hour
- Typically only one active menu exists at a time

**Referenced FRs**: FR-023, FR-024

---

### POST /candidates/{candidate_id}/feedback

**Purpose**: Submit or update feedback for a specific dish

**Auth Required**: Yes | Role: candidate

**Request**:
- **Path Parameters**:
  - `candidate_id`: string (UUID) - ID of the candidate
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: application/json`
- **Body**:
  ```json
  {
    "dish_id": "string - UUID (required)",
    "rating": "number - 1 to 5 stars (optional, null if skipped)",
    "comment": "string - max 500 chars (optional, empty string allowed)",
    "eliminate_vote": "boolean - vote to remove dish from menu (optional, default false)",
    "proposed_dishes": [
      {
        "description": "string - description of proposed alternative (optional)",
        "photo_data": "string - base64 encoded image or multipart reference (optional)"
      }
    ]
  }
  ```

**Response**:
- **Success (201 Created)** (new feedback):
  ```json
  {
    "id": "string - UUID of feedback record",
    "candidate_id": "string - UUID",
    "dish_id": "string - UUID",
    "rating": "number - 1-5 or null",
    "comment": "string",
    "eliminate_vote": "boolean",
    "proposed_dishes": [
      {
        "id": "string - UUID",
        "description": "string",
        "photo_urls": ["string - signed URLs for uploaded photos"]
      }
    ],
    "timestamp": "string - ISO 8601 timestamp",
    "message": "Feedback saved successfully"
  }
  ```
- **Success (200 OK)** (updated feedback):
  ```json
  {
    "id": "string - UUID",
    "candidate_id": "string - UUID",
    "dish_id": "string - UUID",
    "rating": "number - 1-5 or null",
    "comment": "string",
    "eliminate_vote": "boolean",
    "proposed_dishes": [
      {
        "id": "string - UUID",
        "description": "string",
        "photo_urls": ["string"]
      }
    ],
    "timestamp": "string - ISO 8601 timestamp (updated)",
    "message": "Feedback updated successfully"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Rating must be between 1 and 5",
    "code": "INVALID_RATING"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Comment exceeds maximum length of 500 characters",
    "code": "COMMENT_TOO_LONG"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Maximum 5 proposed dish photos allowed",
    "code": "TOO_MANY_PHOTOS"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Photo size exceeds 5 MB limit",
    "code": "PHOTO_TOO_LARGE"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Invalid image format. Supported: JPG, PNG, HEIC",
    "code": "INVALID_IMAGE_FORMAT"
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
    "error": "You can only submit feedback to your own account",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Dish not found",
    "code": "DISH_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to save feedback",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only submit feedback to their own account
- Rating, comment, and eliminate_vote are all optional (partial feedback allowed)
- If feedback for dish already exists, it is updated (upsert behavior)
- Auto-saved as candidate provides input (no explicit save button needed)
- Max 5 proposed dish photos per feedback item
- Photo formats: JPG, PNG, HEIC; max 5 MB each
- Photos stored with encryption at rest
- Cannot modify after final submission

**Referenced FRs**: FR-005, FR-025, FR-026, FR-027, FR-028, FR-029, FR-030, FR-031, FR-032

---

### GET /candidates/{candidate_id}/feedback

**Purpose**: Retrieve all feedback submitted by candidate

**Auth Required**: Yes | Role: candidate (own data) or admin

**Request**:
- **Path Parameters**:
  - `candidate_id`: string (UUID) - ID of the candidate
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
- **Query Parameters**:
  - `dish_id`: string (UUID) - filter by specific dish (optional)

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "candidate_id": "string - UUID",
    "feedback": [
      {
        "id": "string - UUID",
        "dish_id": "string - UUID",
        "dish_name": "string",
        "category_name": "string",
        "rating": "number - 1-5 or null",
        "comment": "string",
        "eliminate_vote": "boolean",
        "proposed_dishes": [
          {
            "id": "string - UUID",
            "description": "string",
            "photo_urls": ["string - signed URLs"]
          }
        ],
        "timestamp": "string - ISO 8601"
      }
    ],
    "total_feedback_items": "number",
    "total_dishes_in_menu": "number"
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
    "error": "You can only view your own feedback",
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
    "error": "Failed to retrieve feedback",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only view their own feedback
- Admins can view any candidate's feedback
- Returns empty array if no feedback submitted
- Includes dish metadata for context
- Signed photo URLs regenerated on each request

**Referenced FRs**: FR-005, FR-029, FR-030, FR-039

---

### POST /candidates/{candidate_id}/submit

**Purpose**: Finalize and submit candidate's complete application (documents, videos, feedback)

**Auth Required**: Yes | Role: candidate

**Request**:
- **Path Parameters**:
  - `candidate_id`: string (UUID) - ID of the candidate
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: application/json`
- **Body**: None (empty)

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "candidate_id": "string - UUID",
    "submission_status": "submitted",
    "submitted_at": "string - ISO 8601 timestamp",
    "summary": {
      "documents_uploaded": {
        "resume": "boolean",
        "cover_letter": "boolean"
      },
      "videos_recorded": "number",
      "total_prompts": "number",
      "feedback_items": "number",
      "total_dishes": "number"
    },
    "message": "Application submitted successfully. You will be contacted via email regarding next steps."
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Cannot submit: missing required documents (resume and cover letter)",
    "code": "INCOMPLETE_DOCUMENTS"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Cannot submit: not all video prompts answered",
    "code": "INCOMPLETE_VIDEOS",
    "details": {
      "completed": 3,
      "required": 5
    }
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Application already submitted",
    "code": "ALREADY_SUBMITTED"
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
    "error": "You can only submit your own application",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to submit application",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only submit their own application
- Required: both resume and cover letter uploaded
- Required: all video prompts answered (one recording per prompt)
- Optional: menu feedback (partial or complete)
- After submission, candidate cannot edit documents, re-record videos, or modify feedback
- Submission status transitions from "incomplete" to "submitted"
- Timestamp recorded for audit trail
- Admin notification triggered (email/dashboard alert)

**Referenced FRs**: FR-005, FR-007, FR-012, FR-032, FR-053, FR-054

---

## Common Error Responses

All endpoints may return:

**401 Unauthorized**:
```json
{
  "error": "Authentication required",
  "code": "AUTHENTICATION_REQUIRED"
}
```

**413 Payload Too Large**:
```json
{
  "error": "Request payload exceeds maximum size",
  "code": "PAYLOAD_TOO_LARGE"
}
```

**429 Too Many Requests**:
```json
{
  "error": "Too many requests. Please try again later.",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": "number - seconds"
}
```

---

## Pydantic Schema Examples

**DocumentUploadRequest**:
```python
from pydantic import BaseModel, Field
from enum import Enum
from fastapi import UploadFile

class DocumentType(str, Enum):
    RESUME = "resume"
    COVER_LETTER = "cover_letter"

class DocumentUploadRequest(BaseModel):
    document_type: DocumentType
    file: UploadFile

    class Config:
        arbitrary_types_allowed = True
```

**FeedbackRequest**:
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List

class ProposedDishInput(BaseModel):
    description: Optional[str] = Field(None, max_length=500)
    photo_data: Optional[str] = None  # base64 or multipart reference

class FeedbackRequest(BaseModel):
    dish_id: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field("", max_length=500)
    eliminate_vote: bool = False
    proposed_dishes: List[ProposedDishInput] = Field(default_factory=list, max_items=5)

    @validator('proposed_dishes')
    def validate_proposed_dishes(cls, v):
        if len(v) > 5:
            raise ValueError('Maximum 5 proposed dishes allowed')
        return v
```

**SubmissionSummary**:
```python
from pydantic import BaseModel

class DocumentsSummary(BaseModel):
    resume: bool
    cover_letter: bool

class SubmissionSummary(BaseModel):
    documents_uploaded: DocumentsSummary
    videos_recorded: int
    total_prompts: int
    feedback_items: int
    total_dishes: int

class SubmissionResponse(BaseModel):
    candidate_id: str
    submission_status: str
    submitted_at: str
    summary: SubmissionSummary
    message: str
```
