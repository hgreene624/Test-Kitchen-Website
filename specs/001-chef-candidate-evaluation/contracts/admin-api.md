# Admin Review & Management API Contract

**Service**: Admin Review & Candidate Management
**Technology**: FastAPI with Pydantic schemas, pagination, filtering, sorting
**Base URL**: `/api/v1/admin`

---

## Endpoints

### GET /admin/candidates

**Purpose**: Retrieve paginated list of all candidates with filtering and sorting

**Auth Required**: Yes | Role: admin

**Request**:
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
- **Query Parameters**:
  - `status`: string - filter by submission status: "incomplete", "submitted", "reviewed", "eliminated", "hired" (optional, comma-separated for multiple)
  - `page`: number - page number (default: 1)
  - `page_size`: number - items per page (default: 20, max: 100)
  - `sort_by`: string - field to sort by: "created_at", "submitted_at", "full_name", "email" (default: "created_at")
  - `sort_order`: string - "asc" or "desc" (default: "desc")
  - `search`: string - search by name or email (optional)

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "candidates": [
      {
        "id": "string - UUID",
        "full_name": "string",
        "email": "string",
        "account_status": "string - 'active', 'unverified', 'rejected'",
        "submission_status": "string - 'incomplete', 'submitted', 'reviewed', 'eliminated', 'hired'",
        "created_at": "string - ISO 8601 timestamp",
        "submitted_at": "string - ISO 8601 timestamp (null if not submitted)",
        "documents_uploaded": {
          "resume": "boolean",
          "cover_letter": "boolean"
        },
        "videos_recorded": "number",
        "total_prompts": "number",
        "feedback_items": "number",
        "total_dishes": "number",
        "completion_percentage": "number - 0-100"
      }
    ],
    "pagination": {
      "page": "number",
      "page_size": "number",
      "total_items": "number",
      "total_pages": "number",
      "has_next": "boolean",
      "has_previous": "boolean"
    },
    "filters_applied": {
      "status": ["string"],
      "search": "string"
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
    "error": "Admin access required",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Invalid query parameter",
    "code": "INVALID_PARAMETER",
    "details": {
      "field": "page_size",
      "message": "page_size must be between 1 and 100"
    }
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to retrieve candidates",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Only admins can access this endpoint
- Default sort: newest candidates first (created_at desc)
- Search queries full_name and email fields (case-insensitive partial match)
- Status filter supports multiple values (e.g., "submitted,reviewed")
- Completion percentage calculated from required items (documents + all video prompts)
- All admin access logged to audit trail

**Referenced FRs**: FR-006, FR-033, FR-034

---

### GET /admin/candidates/{candidate_id}

**Purpose**: Retrieve complete candidate detail including all submission materials

**Auth Required**: Yes | Role: admin

**Request**:
- **Path Parameters**:
  - `candidate_id`: string (UUID) - ID of the candidate
- **Headers**:
  - `Authorization: Bearer {jwt_token}`

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "id": "string - UUID",
    "full_name": "string",
    "email": "string",
    "account_status": "string",
    "submission_status": "string",
    "created_at": "string - ISO 8601 timestamp",
    "submitted_at": "string - ISO 8601 timestamp (null if not submitted)",
    "documents": [
      {
        "id": "string - UUID",
        "document_type": "string - 'resume' or 'cover_letter'",
        "file_name": "string",
        "file_size": "number - bytes",
        "file_url": "string - signed URL for download (1 hour expiry)",
        "uploaded_at": "string - ISO 8601 timestamp"
      }
    ],
    "recordings": [
      {
        "id": "string - UUID",
        "prompt_id": "string - UUID",
        "prompt_text": "string",
        "sequence_order": "number",
        "file_url": "string - signed URL for playback",
        "duration_seconds": "number",
        "upload_timestamp": "string - ISO 8601 timestamp",
        "transcription_status": "string - 'pending', 'processing', 'completed', 'failed', 'unavailable'",
        "transcript": {
          "id": "string - UUID",
          "file_url": "string - signed URL for downloadable .txt file",
          "file_name": "string - formatted as '[Prompt Text] - [Candidate Name].txt'",
          "confidence_score": "number - 0.0 to 1.0",
          "generated_at": "string - ISO 8601 timestamp"
        }
      }
    ],
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
    "summary": {
      "documents_uploaded": 2,
      "videos_recorded": 5,
      "total_prompts": 5,
      "feedback_items": 18,
      "total_dishes": 25,
      "completion_percentage": 100
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
    "error": "Admin access required",
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
    "error": "Failed to retrieve candidate details",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Only admins can access this endpoint
- All signed URLs expire after 1 hour
- Transcript field only present if transcription status is "completed"
- If transcription status is "failed" or "unavailable", video is still accessible for manual review
- All media URLs regenerated on each request
- Access logged to audit trail with admin ID and timestamp

**Referenced FRs**: FR-006, FR-035, FR-036, FR-037, FR-038, FR-039

---

### GET /admin/candidates/{candidate_id}/transcripts/{recording_id}

**Purpose**: Download transcript file for specific video recording

**Auth Required**: Yes | Role: admin

**Request**:
- **Path Parameters**:
  - `candidate_id`: string (UUID) - ID of the candidate
  - `recording_id`: string (UUID) - ID of the video recording
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
- **Query Parameters**:
  - `format`: string - "txt" or "json" (default: "txt")

**Response**:
- **Success (200 OK)** (format=txt):
  ```
  Content-Type: text/plain
  Content-Disposition: attachment; filename="[Prompt Text] - [Candidate Name].txt"

  [Transcribed text content]
  ```
- **Success (200 OK)** (format=json):
  ```json
  {
    "transcript_id": "string - UUID",
    "recording_id": "string - UUID",
    "candidate_id": "string - UUID",
    "candidate_name": "string",
    "prompt_text": "string",
    "text": "string - full transcript",
    "confidence_score": "number - 0.0 to 1.0",
    "duration_seconds": "number",
    "generated_at": "string - ISO 8601 timestamp",
    "file_name": "string - formatted filename"
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
    "error": "Admin access required",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Transcript not found or not yet available",
    "code": "TRANSCRIPT_NOT_FOUND"
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
- Only admins can download transcripts
- Transcript filename formatted as: "[Prompt Text] - [Candidate Name].txt"
- Returns 404 if transcription status is not "completed"
- txt format returns plain text file
- json format returns structured metadata + transcript
- Download logged to audit trail

**Referenced FRs**: FR-006, FR-019, FR-020, FR-038

---

### PUT /admin/candidates/{candidate_id}/status

**Purpose**: Update candidate's submission status (reviewed, eliminated, hired)

**Auth Required**: Yes | Role: admin

**Request**:
- **Path Parameters**:
  - `candidate_id`: string (UUID) - ID of the candidate
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: application/json`
- **Body**:
  ```json
  {
    "status": "string - 'reviewed', 'eliminated', 'hired' (required)",
    "notes": "string - admin's review notes (optional, max 1000 chars)"
  }
  ```

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "candidate_id": "string - UUID",
    "previous_status": "string",
    "new_status": "string",
    "notes": "string",
    "updated_by": "string - admin's full name",
    "updated_at": "string - ISO 8601 timestamp",
    "message": "Candidate status updated successfully"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Invalid status transition",
    "code": "INVALID_STATUS_TRANSITION",
    "details": {
      "current_status": "incomplete",
      "requested_status": "reviewed",
      "message": "Cannot mark candidate as reviewed until they submit their application"
    }
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Invalid status value",
    "code": "INVALID_STATUS",
    "details": {
      "allowed_values": ["reviewed", "eliminated", "hired"]
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
    "error": "Admin access required",
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
    "error": "Failed to update candidate status",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Only admins can update candidate status
- Valid status transitions:
  - "submitted" → "reviewed", "eliminated", "hired"
  - "reviewed" → "eliminated", "hired"
  - Cannot transition from "incomplete" (candidate must submit first)
  - Cannot transition backward (e.g., "hired" → "reviewed")
- Status update logged to audit trail with admin ID, timestamp, and notes
- Optional notes field for admin's review comments (stored but not visible to candidate)

**Referenced FRs**: FR-006, FR-034, FR-055

---

### GET /admin/dishes

**Purpose**: Retrieve dishes with aggregated candidate feedback for gallery or table view

**Auth Required**: Yes | Role: admin

**Request**:
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
- **Query Parameters**:
  - `menu_id`: string (UUID) - filter by menu (optional, defaults to active menu)
  - `category`: string - filter by category name (optional)
  - `view_mode`: string - "gallery" or "table" (affects response structure, default: "gallery")
  - `min_rating`: number - filter dishes with average rating >= value (optional, 1-5)
  - `max_rating`: number - filter dishes with average rating <= value (optional, 1-5)
  - `has_eliminate_votes`: boolean - filter dishes with elimination votes (optional)
  - `has_proposed_dishes`: boolean - filter dishes with proposed alternatives (optional)
  - `sort_by`: string - "average_rating", "feedback_count", "eliminate_votes", "dish_name" (default: "dish_name")
  - `sort_order`: string - "asc" or "desc" (default: "asc")
  - `page`: number - page number (default: 1)
  - `page_size`: number - items per page (default: 50, max: 100)

**Response (view_mode=gallery)**:
- **Success (200 OK)**:
  ```json
  {
    "view_mode": "gallery",
    "dishes": [
      {
        "id": "string - UUID",
        "dish_name": "string",
        "description": "string",
        "category_name": "string",
        "photo_urls": ["string - signed URLs"],
        "feedback_summary": {
          "total_feedback": "number - count of candidates who reviewed this dish",
          "average_rating": "number - 1-5 (null if no ratings)",
          "rating_distribution": {
            "1": "number",
            "2": "number",
            "3": "number",
            "4": "number",
            "5": "number"
          },
          "comment_count": "number",
          "eliminate_vote_count": "number",
          "proposed_dish_count": "number"
        },
        "candidate_previews": [
          {
            "candidate_id": "string - UUID",
            "candidate_name": "string",
            "rating": "number - 1-5 or null",
            "has_comment": "boolean",
            "eliminate_vote": "boolean"
          }
        ]
      }
    ],
    "pagination": {
      "page": "number",
      "page_size": "number",
      "total_items": "number",
      "total_pages": "number"
    },
    "filters_applied": {
      "category": "string",
      "min_rating": "number",
      "max_rating": "number"
    }
  }
  ```
- **Response (view_mode=table)**:
- **Success (200 OK)**:
  ```json
  {
    "view_mode": "table",
    "dishes": [
      {
        "id": "string - UUID",
        "dish_name": "string",
        "category_name": "string",
        "average_rating": "number - 1-5 (null if no ratings)",
        "comment_count": "number",
        "eliminate_vote_count": "number",
        "proposed_dish_count": "number",
        "total_feedback": "number",
        "photo_url": "string - primary photo signed URL"
      }
    ],
    "pagination": {
      "page": "number",
      "page_size": "number",
      "total_items": "number",
      "total_pages": "number"
    },
    "filters_applied": {
      "category": "string",
      "min_rating": "number",
      "max_rating": "number"
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
    "error": "Admin access required",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Invalid view mode",
    "code": "INVALID_VIEW_MODE",
    "details": {
      "allowed_values": ["gallery", "table"]
    }
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to retrieve dish feedback",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Only admins can access this endpoint
- Gallery view includes candidate previews (up to 5 most recent)
- Table view optimized for sorting/filtering (less data per row)
- Aggregations calculated from all submitted candidates only (not incomplete submissions)
- Filters can be combined (e.g., category + min_rating)
- Average rating rounded to 1 decimal place
- Pagination required for performance with large datasets

**Referenced FRs**: FR-006, FR-040, FR-041, FR-042, FR-043

---

### GET /admin/dishes/{dish_id}/feedback

**Purpose**: Retrieve detailed aggregated feedback from all candidates for a specific dish

**Auth Required**: Yes | Role: admin

**Request**:
- **Path Parameters**:
  - `dish_id`: string (UUID) - ID of the dish
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
- **Query Parameters**:
  - `include_proposed_dishes`: boolean - include proposed dish photos (default: true)

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "dish_id": "string - UUID",
    "dish_name": "string",
    "description": "string",
    "category_name": "string",
    "photo_urls": ["string - signed URLs"],
    "feedback_summary": {
      "total_feedback": "number",
      "average_rating": "number - 1-5 (null if no ratings)",
      "rating_distribution": {
        "1": "number",
        "2": "number",
        "3": "number",
        "4": "number",
        "5": "number"
      },
      "comment_count": "number",
      "eliminate_vote_count": "number",
      "proposed_dish_count": "number"
    },
    "candidate_feedback": [
      {
        "candidate_id": "string - UUID",
        "candidate_name": "string",
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
    "error": "Admin access required",
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
    "error": "Failed to retrieve dish feedback",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Only admins can access this endpoint
- Shows all candidate feedback for this specific dish
- Candidates ordered by timestamp (most recent first)
- Includes candidates who provided any feedback (rating, comment, eliminate vote, or proposed dishes)
- If include_proposed_dishes=false, proposed_dishes array is excluded for faster loading
- All signed URLs expire after 1 hour

**Referenced FRs**: FR-006, FR-044, FR-045

---

### GET /admin/prompts

**Purpose**: Retrieve all interview prompts (active and inactive) with metadata

**Auth Required**: Yes | Role: admin

**Request**:
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
- **Query Parameters**:
  - `active_only`: boolean - filter to only active prompts (default: false)

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "prompts": [
      {
        "id": "string - UUID",
        "prompt_text": "string",
        "sequence_order": "number",
        "time_limit_seconds": "number - null if no limit",
        "active": "boolean",
        "created_at": "string - ISO 8601 timestamp",
        "modified_at": "string - ISO 8601 timestamp (null if never modified)",
        "usage_count": "number - count of candidates who answered this prompt"
      }
    ],
    "total_prompts": "number",
    "active_prompts": "number"
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
    "error": "Admin access required",
    "code": "INSUFFICIENT_PERMISSIONS"
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
- Only admins can access this endpoint
- Prompts ordered by sequence_order ascending
- usage_count shows how many candidates have recorded responses (helps prevent deletion of used prompts)
- Active prompts are shown to new candidates
- Inactive prompts are historical (removed but retained for data integrity)

**Referenced FRs**: FR-006, FR-046

---

### POST /admin/prompts

**Purpose**: Create a new interview prompt

**Auth Required**: Yes | Role: admin

**Request**:
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: application/json`
- **Body**:
  ```json
  {
    "prompt_text": "string - interview question (required, min 10 chars, max 500 chars)",
    "sequence_order": "number - position in wizard (required, positive integer)",
    "time_limit_seconds": "number - max recording time (optional, default 300)"
  }
  ```

**Response**:
- **Success (201 Created)**:
  ```json
  {
    "id": "string - UUID",
    "prompt_text": "string",
    "sequence_order": "number",
    "time_limit_seconds": "number",
    "active": "boolean - true",
    "created_at": "string - ISO 8601 timestamp",
    "message": "Interview prompt created successfully"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Prompt text must be between 10 and 500 characters",
    "code": "INVALID_PROMPT_TEXT"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Sequence order already exists. Use reorder endpoint to adjust positions.",
    "code": "DUPLICATE_SEQUENCE_ORDER"
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
    "error": "Admin access required",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to create prompt",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Only admins can create prompts
- Prompt text required (10-500 characters)
- Sequence order must be unique among active prompts
- Default time limit is 300 seconds (5 minutes)
- New prompts are active by default
- Existing prompts with same or higher sequence_order are automatically reordered (+1)
- Action logged to audit trail

**Referenced FRs**: FR-006, FR-047, FR-055

---

### PUT /admin/prompts/{prompt_id}

**Purpose**: Update existing interview prompt text or time limit

**Auth Required**: Yes | Role: admin

**Request**:
- **Path Parameters**:
  - `prompt_id`: string (UUID) - ID of the prompt
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: application/json`
- **Body**:
  ```json
  {
    "prompt_text": "string - updated question (optional, min 10 chars, max 500 chars)",
    "time_limit_seconds": "number - updated time limit (optional)"
  }
  ```

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "id": "string - UUID",
    "prompt_text": "string",
    "sequence_order": "number",
    "time_limit_seconds": "number",
    "active": "boolean",
    "modified_at": "string - ISO 8601 timestamp",
    "message": "Prompt updated successfully"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Cannot edit prompt that has been answered by candidates",
    "code": "PROMPT_IN_USE",
    "details": {
      "usage_count": 15,
      "message": "Create a new prompt instead or deactivate this one"
    }
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Prompt text must be between 10 and 500 characters",
    "code": "INVALID_PROMPT_TEXT"
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
    "error": "Admin access required",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Prompt not found",
    "code": "PROMPT_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to update prompt",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Only admins can update prompts
- Cannot edit prompts that have been answered by any candidate (usage_count > 0)
- If prompt is in use, admin must create new prompt or deactivate existing one
- Changes only affect new candidates (existing candidates see original prompts)
- Action logged to audit trail

**Referenced FRs**: FR-006, FR-048, FR-051, FR-055

---

### DELETE /admin/prompts/{prompt_id}

**Purpose**: Remove interview prompt from active rotation (soft delete)

**Auth Required**: Yes | Role: admin

**Request**:
- **Path Parameters**:
  - `prompt_id`: string (UUID) - ID of the prompt
- **Headers**:
  - `Authorization: Bearer {jwt_token}`

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "id": "string - UUID",
    "prompt_text": "string",
    "active": "boolean - false",
    "message": "Prompt deactivated successfully. Historical responses preserved."
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
    "error": "Admin access required",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (404 Not Found)**:
  ```json
  {
    "error": "Prompt not found",
    "code": "PROMPT_NOT_FOUND"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to delete prompt",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Only admins can delete prompts
- Soft delete: prompt marked as inactive (active=false)
- Historical candidate responses are preserved (not deleted)
- Inactive prompts not shown to new candidates
- Sequence order gaps left by deletion are automatically filled (other prompts reordered)
- Action logged to audit trail

**Referenced FRs**: FR-006, FR-049, FR-051, FR-055

---

### PUT /admin/prompts/reorder

**Purpose**: Reorder interview prompts via drag-and-drop or up/down controls

**Auth Required**: Yes | Role: admin

**Request**:
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: application/json`
- **Body**:
  ```json
  {
    "prompt_order": [
      {
        "id": "string - UUID",
        "sequence_order": "number - new position (1-based)"
      }
    ]
  }
  ```

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "prompts": [
      {
        "id": "string - UUID",
        "prompt_text": "string",
        "sequence_order": "number",
        "active": "boolean"
      }
    ],
    "message": "Prompts reordered successfully"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Invalid reorder request: duplicate sequence orders",
    "code": "DUPLICATE_SEQUENCE_ORDER"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Invalid reorder request: missing prompts",
    "code": "MISSING_PROMPTS",
    "details": {
      "message": "All active prompts must be included in reorder request"
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
    "error": "Admin access required",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to reorder prompts",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Only admins can reorder prompts
- All active prompts must be included in request
- Sequence orders must be unique and consecutive (1, 2, 3, ...)
- Changes only affect new candidates (existing candidates see original order)
- Reorder operation is atomic (all-or-nothing)
- Action logged to audit trail

**Referenced FRs**: FR-006, FR-050, FR-051, FR-055

---

## Common Error Responses

**401 Unauthorized**:
```json
{
  "error": "Authentication required",
  "code": "AUTHENTICATION_REQUIRED"
}
```

**403 Forbidden**:
```json
{
  "error": "Admin access required",
  "code": "INSUFFICIENT_PERMISSIONS"
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

**CandidateListItem**:
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DocumentsSummary(BaseModel):
    resume: bool
    cover_letter: bool

class CandidateListItem(BaseModel):
    id: str
    full_name: str
    email: str
    account_status: str
    submission_status: str
    created_at: datetime
    submitted_at: Optional[datetime]
    documents_uploaded: DocumentsSummary
    videos_recorded: int
    total_prompts: int
    feedback_items: int
    total_dishes: int
    completion_percentage: int
```

**DishFeedbackSummary**:
```python
from pydantic import BaseModel
from typing import Dict, Optional

class RatingDistribution(BaseModel):
    one: int = Field(..., alias="1")
    two: int = Field(..., alias="2")
    three: int = Field(..., alias="3")
    four: int = Field(..., alias="4")
    five: int = Field(..., alias="5")

class FeedbackSummary(BaseModel):
    total_feedback: int
    average_rating: Optional[float]
    rating_distribution: RatingDistribution
    comment_count: int
    eliminate_vote_count: int
    proposed_dish_count: int

class DishGalleryItem(BaseModel):
    id: str
    dish_name: str
    description: str
    category_name: str
    photo_urls: list[str]
    feedback_summary: FeedbackSummary
```

**PromptCreate**:
```python
from pydantic import BaseModel, Field

class PromptCreate(BaseModel):
    prompt_text: str = Field(..., min_length=10, max_length=500)
    sequence_order: int = Field(..., gt=0)
    time_limit_seconds: int = Field(default=300, gt=0, le=600)
```
