# Media Upload & Access API Contract

**Service**: Media Upload, Storage, and Signed URL Access
**Technology**: FastAPI with S3-compatible storage, multipart/resumable uploads
**Base URL**: `/api/v1/media`

---

## Endpoints

### POST /media/initiate-upload

**Purpose**: Initialize chunked/resumable upload session for large video files

**Auth Required**: Yes | Role: candidate

**Request**:
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: application/json`
- **Body**:
  ```json
  {
    "file_name": "string - original filename (required)",
    "file_size": "number - total file size in bytes (required)",
    "content_type": "string - MIME type (e.g., 'video/webm', 'video/mp4') (required)",
    "media_type": "string - 'video', 'document', 'photo' (required)",
    "candidate_id": "string - UUID (required)",
    "prompt_id": "string - UUID (required for videos, null for other types)"
  }
  ```

**Response**:
- **Success (201 Created)**:
  ```json
  {
    "upload_id": "string - UUID of upload session",
    "file_id": "string - UUID of file record (created but not finalized)",
    "chunk_size": "number - recommended chunk size in bytes (default 5242880 = 5MB)",
    "total_chunks": "number - calculated from file_size / chunk_size",
    "expires_at": "string - ISO 8601 timestamp (upload session expires in 24 hours)",
    "message": "Upload session initiated. Begin uploading chunks."
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "File size exceeds maximum allowed",
    "code": "FILE_TOO_LARGE",
    "details": {
      "max_size_bytes": 104857600,
      "max_size_mb": 100,
      "uploaded_size_mb": 150
    }
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Invalid content type for media type",
    "code": "INVALID_CONTENT_TYPE",
    "details": {
      "media_type": "video",
      "allowed_types": ["video/webm", "video/mp4"]
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
    "error": "You can only upload media to your own account",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to initiate upload",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only initiate uploads for their own account (candidate_id must match JWT)
- Maximum file sizes by media type:
  - Video: 100 MB (~5 minutes at standard quality)
  - Document: 10 MB
  - Photo: 5 MB
- Allowed content types by media type:
  - Video: video/webm, video/mp4
  - Document: application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document
  - Photo: image/jpeg, image/png, image/heic
- Upload session expires after 24 hours if not completed
- Chunk size recommendation: 5 MB (optimal for network performance)
- File record created in "uploading" state (not accessible until finalized)

**Referenced FRs**: FR-005, FR-008, FR-015, FR-031

---

### POST /media/upload-chunk

**Purpose**: Upload a single chunk of file data to resumable upload session

**Auth Required**: Yes | Role: candidate

**Request**:
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: multipart/form-data`
- **Body** (multipart/form-data):
  ```
  upload_id: string (UUID) - upload session ID from initiate-upload (required)
  chunk_index: number - zero-based chunk index (required)
  chunk_data: binary - chunk file data (required)
  chunk_hash: string - MD5 or SHA256 hash for integrity verification (optional but recommended)
  ```

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "upload_id": "string - UUID",
    "chunk_index": "number",
    "chunk_size": "number - bytes uploaded in this chunk",
    "uploaded_chunks": ["number - array of completed chunk indexes"],
    "total_chunks": "number",
    "bytes_uploaded": "number - cumulative bytes uploaded",
    "total_bytes": "number - total file size",
    "progress_percentage": "number - 0-100",
    "message": "Chunk uploaded successfully"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Invalid chunk index",
    "code": "INVALID_CHUNK_INDEX",
    "details": {
      "chunk_index": 10,
      "total_chunks": 8,
      "message": "Chunk index exceeds total chunks"
    }
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Chunk hash mismatch",
    "code": "CHUNK_INTEGRITY_ERROR",
    "details": {
      "expected_hash": "abc123...",
      "computed_hash": "def456...",
      "message": "Chunk data corrupted during upload. Please retry this chunk."
    }
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Chunk already uploaded",
    "code": "DUPLICATE_CHUNK",
    "details": {
      "chunk_index": 3,
      "message": "This chunk has already been successfully uploaded. Continue with next chunk."
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
    "error": "You can only upload to your own upload sessions",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Upload session not found or expired",
    "code": "UPLOAD_SESSION_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to upload chunk",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only upload chunks to their own sessions
- Chunks can be uploaded in any order (supports parallel uploads)
- Duplicate chunks are idempotent (re-uploading same chunk returns success)
- Optional chunk hash validation for data integrity
- Progress percentage calculated as (bytes_uploaded / total_bytes) * 100
- Upload session state persisted to support resume after network interruption
- Last chunk may be smaller than chunk_size

**Referenced FRs**: FR-005, FR-015

---

### POST /media/finalize-upload

**Purpose**: Complete chunked upload session and make file accessible

**Auth Required**: Yes | Role: candidate

**Request**:
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: application/json`
- **Body**:
  ```json
  {
    "upload_id": "string - UUID of upload session (required)",
    "file_hash": "string - MD5 or SHA256 hash of complete file (optional but recommended)"
  }
  ```

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "file_id": "string - UUID of finalized file",
    "upload_id": "string - UUID (now completed)",
    "file_url": "string - signed URL for accessing file (1 hour expiry)",
    "file_size": "number - bytes",
    "file_name": "string",
    "content_type": "string",
    "uploaded_at": "string - ISO 8601 timestamp",
    "message": "Upload completed successfully",
    "next_steps": {
      "transcription_job_id": "string - UUID (only for videos)",
      "transcription_status": "string - 'pending' (only for videos)"
    }
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Upload incomplete: missing chunks",
    "code": "INCOMPLETE_UPLOAD",
    "details": {
      "uploaded_chunks": [0, 1, 2, 4, 5],
      "missing_chunks": [3],
      "total_chunks": 6,
      "message": "Upload all chunks before finalizing"
    }
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "File hash mismatch",
    "code": "FILE_INTEGRITY_ERROR",
    "details": {
      "expected_hash": "abc123...",
      "computed_hash": "def456...",
      "message": "Complete file integrity check failed. Please re-upload."
    }
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Upload already finalized",
    "code": "UPLOAD_ALREADY_FINALIZED"
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
    "error": "You can only finalize your own uploads",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Upload session not found or expired",
    "code": "UPLOAD_SESSION_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to finalize upload",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only finalize their own upload sessions
- All chunks must be uploaded before finalizing
- Optional file hash validation for complete file integrity
- File record status transitions from "uploading" to "completed"
- For videos: transcription job automatically triggered after finalization
- Signed URL generated for immediate file access
- Upload session cleaned up after finalization (chunks combined into single file)
- File stored with encryption at rest

**Referenced FRs**: FR-005, FR-010, FR-015, FR-018

---

### GET /media/{file_id}/signed-url

**Purpose**: Generate time-limited signed URL for secure file access

**Auth Required**: Yes | Role: candidate (own files) or admin

**Request**:
- **Path Parameters**:
  - `file_id`: string (UUID) - ID of the file
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
- **Query Parameters**:
  - `expiry_minutes`: number - URL validity duration in minutes (default: 60, max: 1440 = 24 hours)
  - `download`: boolean - force download instead of inline display (default: false)

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "file_id": "string - UUID",
    "file_name": "string",
    "file_size": "number - bytes",
    "content_type": "string",
    "signed_url": "string - time-limited URL for file access",
    "expires_at": "string - ISO 8601 timestamp when URL expires",
    "is_download": "boolean - whether URL forces download"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Expiry duration exceeds maximum allowed (1440 minutes)",
    "code": "INVALID_EXPIRY_DURATION"
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
    "error": "You can only access your own files",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "File not found",
    "code": "FILE_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to generate signed URL",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only access their own files
- Admins can access any file
- Default expiry: 1 hour (60 minutes)
- Maximum expiry: 24 hours (1440 minutes)
- download=true adds Content-Disposition: attachment header to force download
- download=false allows inline display in browser (useful for videos/images)
- Signed URL includes cryptographic signature to prevent tampering
- URL is single-use or time-limited (depends on storage backend)
- Access logged to audit trail for admin requests

**Referenced FRs**: FR-005, FR-006, FR-036, FR-037

---

### DELETE /media/{file_id}

**Purpose**: Delete file from storage (admin-only or candidate before submission)

**Auth Required**: Yes | Role: candidate (own files, pre-submission) or admin

**Request**:
- **Path Parameters**:
  - `file_id`: string (UUID) - ID of the file
- **Headers**:
  - `Authorization: Bearer {jwt_token}`

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "file_id": "string - UUID",
    "file_name": "string",
    "deleted_at": "string - ISO 8601 timestamp",
    "message": "File deleted successfully"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Cannot delete file after submission",
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
    "error": "You can only delete your own files",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "File not found",
    "code": "FILE_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to delete file",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only delete their own files before final submission
- Admins can delete any file (for data retention compliance)
- Cannot delete files after candidate submits application (enforces immutability)
- File removed from storage backend
- Database record marked as deleted (soft delete) or removed (hard delete)
- Associated records updated (e.g., VideoRecording.file_url set to null)
- Deletion logged to audit trail

**Referenced FRs**: FR-005, FR-006, FR-054, FR-056

---

### GET /media/upload-status/{upload_id}

**Purpose**: Check status of ongoing or completed upload session (for resume after interruption)

**Auth Required**: Yes | Role: candidate

**Request**:
- **Path Parameters**:
  - `upload_id`: string (UUID) - ID of upload session
- **Headers**:
  - `Authorization: Bearer {jwt_token}`

**Response**:
- **Success (200 OK)** (upload in progress):
  ```json
  {
    "upload_id": "string - UUID",
    "file_id": "string - UUID",
    "status": "string - 'in_progress'",
    "file_name": "string",
    "file_size": "number - total bytes",
    "chunk_size": "number",
    "total_chunks": "number",
    "uploaded_chunks": ["number - array of completed chunk indexes"],
    "missing_chunks": ["number - array of pending chunk indexes"],
    "bytes_uploaded": "number",
    "progress_percentage": "number - 0-100",
    "created_at": "string - ISO 8601 timestamp",
    "expires_at": "string - ISO 8601 timestamp"
  }
  ```
- **Success (200 OK)** (upload completed):
  ```json
  {
    "upload_id": "string - UUID",
    "file_id": "string - UUID",
    "status": "string - 'completed'",
    "file_url": "string - signed URL",
    "completed_at": "string - ISO 8601 timestamp"
  }
  ```
- **Success (200 OK)** (upload expired):
  ```json
  {
    "upload_id": "string - UUID",
    "status": "string - 'expired'",
    "expired_at": "string - ISO 8601 timestamp",
    "message": "Upload session expired. Please initiate a new upload."
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
    "error": "You can only check status of your own uploads",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Upload session not found",
    "code": "UPLOAD_SESSION_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to retrieve upload status",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Candidates can only check status of their own upload sessions
- Returns list of completed and missing chunks for resume capability
- Client can resume by uploading only missing chunks
- Upload session expires 24 hours after creation if not finalized
- Status polling interval recommendation: 5-10 seconds during active upload

**Referenced FRs**: FR-005, FR-015

---

## Upload Flow Example

**Complete resumable video upload workflow**:

1. **Initiate Upload**:
   ```
   POST /media/initiate-upload
   Body: { file_name: "interview.webm", file_size: 52428800, content_type: "video/webm", media_type: "video", candidate_id: "...", prompt_id: "..." }
   Response: { upload_id: "...", chunk_size: 5242880, total_chunks: 10 }
   ```

2. **Upload Chunks** (parallel or sequential):
   ```
   POST /media/upload-chunk (chunk 0)
   POST /media/upload-chunk (chunk 1)
   ...
   POST /media/upload-chunk (chunk 9)
   ```

3. **Check Status** (optional, for resume after interruption):
   ```
   GET /media/upload-status/{upload_id}
   Response: { uploaded_chunks: [0,1,2,3,4], missing_chunks: [5,6,7,8,9] }
   ```

4. **Finalize Upload**:
   ```
   POST /media/finalize-upload
   Body: { upload_id: "..." }
   Response: { file_id: "...", file_url: "...", transcription_job_id: "..." }
   ```

5. **Access File** (later):
   ```
   GET /media/{file_id}/signed-url
   Response: { signed_url: "https://storage.../interview.webm?signature=..." }
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

**InitiateUploadRequest**:
```python
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class MediaType(str, Enum):
    VIDEO = "video"
    DOCUMENT = "document"
    PHOTO = "photo"

class InitiateUploadRequest(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0)
    content_type: str
    media_type: MediaType
    candidate_id: str
    prompt_id: Optional[str] = None

    @validator('file_size')
    def validate_file_size(cls, v, values):
        media_type = values.get('media_type')
        max_sizes = {
            MediaType.VIDEO: 104857600,  # 100 MB
            MediaType.DOCUMENT: 10485760,  # 10 MB
            MediaType.PHOTO: 5242880  # 5 MB
        }
        if v > max_sizes.get(media_type, 10485760):
            raise ValueError(f'File size exceeds maximum for {media_type}')
        return v
```

**ChunkUploadRequest**:
```python
from pydantic import BaseModel, Field
from fastapi import UploadFile
from typing import Optional

class ChunkUploadRequest(BaseModel):
    upload_id: str
    chunk_index: int = Field(..., ge=0)
    chunk_data: UploadFile
    chunk_hash: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
```

**UploadStatusResponse**:
```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UploadStatusResponse(BaseModel):
    upload_id: str
    file_id: str
    status: str  # 'in_progress', 'completed', 'expired'
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    chunk_size: Optional[int] = None
    total_chunks: Optional[int] = None
    uploaded_chunks: Optional[List[int]] = None
    missing_chunks: Optional[List[int]] = None
    bytes_uploaded: Optional[int] = None
    progress_percentage: Optional[float] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    file_url: Optional[str] = None
```

**SignedUrlResponse**:
```python
from pydantic import BaseModel
from datetime import datetime

class SignedUrlResponse(BaseModel):
    file_id: str
    file_name: str
    file_size: int
    content_type: str
    signed_url: str
    expires_at: datetime
    is_download: bool
```
