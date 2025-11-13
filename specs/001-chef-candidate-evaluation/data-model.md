# Data Model: Chef Candidate Evaluation Platform

**Database**: PostgreSQL
**ORM**: SQLAlchemy 2.0 (async)
**Driver**: asyncpg
**Date**: 2025-11-13

## Overview

This document defines the canonical data model for the Chef Candidate Evaluation Platform. All entities use UUID primary keys for distributed system compatibility, include audit timestamps (created_at, updated_at), and enforce referential integrity through foreign key constraints.

**Design Principles**:
- Immutability: Candidate submissions cannot be modified after final submission
- Audit Trail: All state transitions and admin actions are logged with timestamps
- Partial Data: Candidates can skip dishes (feedback is optional per dish)
- Graceful Degradation: Transcription failures do not block candidate progression
- Role-Based Access: Candidates can only access their own data; admins have read-only review access

---

## Entity Schemas

### 1. Candidate

**Purpose**: Represents a chef applicant with account credentials, submission status, and audit trail.

**Fields**:
| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique candidate identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | Candidate's email address for authentication |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hashed password (not stored in plain text) |
| full_name | VARCHAR(255) | NULL | Candidate's full name (captured during profile setup) |
| phone | VARCHAR(50) | NULL | Optional contact phone number |
| account_status | ENUM | NOT NULL, DEFAULT 'unverified', INDEX | Account verification state (see state transitions below) |
| submission_status | ENUM | NOT NULL, DEFAULT 'incomplete', INDEX | Application progress state (see state transitions below) |
| email_verified_at | TIMESTAMP | NULL | Timestamp of email verification completion |
| submitted_at | TIMESTAMP | NULL | Timestamp when candidate submitted final application |
| reviewed_at | TIMESTAMP | NULL | Timestamp when admin completed review |
| final_decision | ENUM | NULL | Hiring decision: 'eliminated', 'hired', NULL (pending) |
| final_decision_at | TIMESTAMP | NULL | Timestamp of hiring decision |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Account creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

**Relationships**:
- One-to-many with Document (CASCADE on delete)
- One-to-many with VideoRecording (CASCADE on delete)
- One-to-many with Feedback (CASCADE on delete)
- One-to-many with ProposedDish (CASCADE on delete)
- One-to-many with AuditLog (CASCADE on delete)

**Indexes**:
- `idx_candidate_email` (email) - Fast lookup for authentication
- `idx_candidate_account_status` (account_status) - Filter verified candidates
- `idx_candidate_submission_status` (submission_status) - Admin dashboard filtering
- `idx_candidate_created_at` (created_at DESC) - Sort by application date

**State Transitions**:

**account_status ENUM**: `('unverified', 'active', 'suspended')`
```
unverified (initial) → active (email verified)
active → suspended (admin action)
suspended → active (admin reactivation)
```

**submission_status ENUM**: `('incomplete', 'submitted', 'under_review', 'reviewed')`
```
incomplete (initial) → submitted (candidate final submission)
submitted → under_review (admin begins review)
under_review → reviewed (admin completes review)
```

**final_decision ENUM**: `('eliminated', 'hired', NULL)`
- Can only be set when submission_status = 'reviewed'

**Validation Rules**:
- Email must match regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- Password must be hashed with bcrypt (min 8 chars, uppercase, lowercase, number, symbol enforced at API layer)
- email_verified_at must be NULL when account_status = 'unverified'
- submitted_at must be NULL when submission_status = 'incomplete'
- final_decision can only be set when submission_status = 'reviewed'
- Candidates cannot modify data when submission_status IN ('submitted', 'under_review', 'reviewed')

---

### 2. Document

**Purpose**: Stores uploaded resume and cover letter files with metadata for candidate profile.

**Fields**:
| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique document identifier |
| candidate_id | UUID | FOREIGN KEY (candidate.id) ON DELETE CASCADE, NOT NULL, INDEX | Owner of the document |
| document_type | ENUM | NOT NULL | Type of document: 'resume', 'cover_letter' |
| file_url | TEXT | NOT NULL | S3 presigned URL or object key for retrieval |
| file_name | VARCHAR(255) | NOT NULL | Original filename uploaded by candidate |
| file_size_bytes | INTEGER | NOT NULL, CHECK (file_size_bytes <= 10485760) | File size in bytes (max 10 MB) |
| mime_type | VARCHAR(100) | NOT NULL | MIME type: 'application/pdf', 'application/msword', etc. |
| s3_bucket | VARCHAR(255) | NOT NULL | S3 bucket name for file storage |
| s3_key | TEXT | NOT NULL | S3 object key path |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Upload timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

**Relationships**:
- Many-to-one with Candidate (candidate_id)

**Indexes**:
- `idx_document_candidate_id` (candidate_id) - Fast lookup of candidate's documents
- `idx_document_type` (candidate_id, document_type) - Unique constraint enforcement helper

**Unique Constraints**:
- `unique_candidate_document_type` (candidate_id, document_type) - Each candidate can have only one resume and one cover letter

**Validation Rules**:
- file_size_bytes must be <= 10,485,760 bytes (10 MB)
- mime_type must be one of: 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
- file_url must be accessible S3 URL or valid S3 key
- Candidates can re-upload (update) documents only when submission_status = 'incomplete'

**ON DELETE Behavior**:
- ON DELETE CASCADE: Deleting a candidate deletes all their documents

---

### 3. InterviewPrompt

**Purpose**: Defines video interview questions presented to candidates in sequential wizard flow.

**Fields**:
| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique prompt identifier |
| prompt_text | TEXT | NOT NULL | Interview question text displayed to candidate |
| sequence_order | INTEGER | NOT NULL, UNIQUE, INDEX | Display order in wizard (1-indexed) |
| time_limit_seconds | INTEGER | NULL, CHECK (time_limit_seconds <= 300) | Optional time limit (max 5 minutes = 300 seconds) |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE, INDEX | Whether prompt is shown to new candidates |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Prompt creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |
| created_by_admin_id | UUID | FOREIGN KEY (admin_user.id) ON DELETE SET NULL, NULL | Admin who created the prompt |

**Relationships**:
- One-to-many with VideoRecording (RESTRICT on delete to preserve historical responses)
- Many-to-one with AdminUser (created_by_admin_id)

**Indexes**:
- `idx_prompt_sequence_order` (sequence_order) - Fast sequential retrieval
- `idx_prompt_is_active` (is_active, sequence_order) - Filter active prompts in order

**Validation Rules**:
- sequence_order must be positive integer (1, 2, 3, ...)
- time_limit_seconds, if set, must be between 30 and 300 seconds
- prompt_text must be non-empty (min 10 characters)
- Only active prompts (is_active = TRUE) are shown to candidates who have not started the interview
- Candidates who have started interviews see the original prompt set (snapshot at interview start time)

**ON DELETE Behavior**:
- ON DELETE RESTRICT: Cannot delete prompts with existing VideoRecording responses
- created_by_admin_id ON DELETE SET NULL: Preserve prompt if admin is deleted

**State Transitions**:
- Admins can reorder prompts (update sequence_order)
- Admins can deactivate prompts (is_active = FALSE) without deleting historical responses
- Prompt changes only apply to new candidate interviews (existing candidates see original prompts)

---

### 4. VideoRecording

**Purpose**: Stores candidate's video responses to interview prompts with transcription status tracking.

**Fields**:
| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique recording identifier |
| candidate_id | UUID | FOREIGN KEY (candidate.id) ON DELETE CASCADE, NOT NULL, INDEX | Candidate who recorded the video |
| prompt_id | UUID | FOREIGN KEY (interview_prompt.id) ON DELETE RESTRICT, NOT NULL, INDEX | Interview question being answered |
| file_url | TEXT | NOT NULL | S3 presigned URL or object key for video file |
| file_name | VARCHAR(255) | NOT NULL | Original filename or generated name |
| file_size_bytes | BIGINT | NOT NULL | Video file size in bytes |
| duration_seconds | INTEGER | NOT NULL, CHECK (duration_seconds <= 300) | Video duration (max 5 minutes) |
| mime_type | VARCHAR(100) | NOT NULL | MIME type: 'video/webm', 'video/mp4' |
| s3_bucket | VARCHAR(255) | NOT NULL | S3 bucket name for video storage |
| s3_key | TEXT | NOT NULL | S3 object key path |
| transcription_status | ENUM | NOT NULL, DEFAULT 'pending', INDEX | Transcription processing state (see state transitions) |
| transcription_started_at | TIMESTAMP | NULL | Timestamp when transcription job started |
| transcription_completed_at | TIMESTAMP | NULL | Timestamp when transcription completed |
| transcription_error | TEXT | NULL | Error message if transcription failed |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Upload timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

**Relationships**:
- Many-to-one with Candidate (candidate_id)
- Many-to-one with InterviewPrompt (prompt_id)
- One-to-one with Transcript (CASCADE on delete)

**Indexes**:
- `idx_video_candidate_id` (candidate_id) - Fast lookup of candidate's videos
- `idx_video_transcription_status` (transcription_status, created_at) - Find pending transcription jobs
- `idx_video_candidate_prompt` (candidate_id, prompt_id) - Unique constraint enforcement

**Unique Constraints**:
- `unique_candidate_prompt_response` (candidate_id, prompt_id) - Each candidate can have only one response per prompt

**State Transitions**:

**transcription_status ENUM**: `('pending', 'processing', 'completed', 'failed', 'unavailable')`
```
pending (initial) → processing (ARQ job started)
processing → completed (transcript generated successfully)
processing → failed (transcription error, retry eligible)
processing → unavailable (max retries exceeded or service unavailable)
pending → unavailable (graceful degradation if service down)
```

**Validation Rules**:
- duration_seconds must be <= 300 (5 minutes)
- mime_type must be one of: 'video/webm', 'video/mp4'
- transcription_status = 'completed' requires corresponding Transcript record
- transcription_status = 'failed' or 'unavailable' allows candidate to proceed (graceful degradation)
- Candidates can re-record (update) videos only when submission_status = 'incomplete'

**ON DELETE Behavior**:
- ON DELETE CASCADE: Deleting a candidate deletes all their videos
- ON DELETE RESTRICT: Cannot delete interview prompts with existing responses

---

### 5. Transcript

**Purpose**: Stores transcribed text content from video recordings with confidence metrics.

**Fields**:
| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique transcript identifier |
| video_recording_id | UUID | FOREIGN KEY (video_recording.id) ON DELETE CASCADE, UNIQUE, NOT NULL, INDEX | Associated video recording |
| transcript_text | TEXT | NOT NULL | Full transcribed text content |
| confidence_score | DECIMAL(3,2) | NOT NULL, CHECK (confidence_score >= 0 AND confidence_score <= 1) | Average word-level confidence (0.0-1.0) |
| word_count | INTEGER | NOT NULL | Number of words in transcript |
| file_url | TEXT | NOT NULL | S3 presigned URL or object key for downloadable .txt file |
| file_name | VARCHAR(255) | NOT NULL | Formatted name: "{prompt_text} - {candidate_name}.txt" |
| s3_bucket | VARCHAR(255) | NOT NULL | S3 bucket name for transcript file storage |
| s3_key | TEXT | NOT NULL | S3 object key path |
| provider | VARCHAR(50) | NOT NULL, DEFAULT 'assemblyai' | Transcription service used |
| provider_metadata | JSONB | NULL | Provider-specific data (word timestamps, speaker labels, etc.) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Transcript generation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

**Relationships**:
- One-to-one with VideoRecording (video_recording_id)

**Indexes**:
- `idx_transcript_video_recording_id` (video_recording_id) - Fast lookup via video
- `idx_transcript_confidence_score` (confidence_score) - Find low-quality transcripts for review

**Validation Rules**:
- confidence_score must be between 0.0 and 1.0
- confidence_score < 0.75 should flag transcript as "low quality" in admin UI
- file_name must follow format: "{prompt_text} - {candidate_full_name}.txt"
- transcript_text must be non-empty if confidence_score > 0
- provider_metadata should include word-level timestamps and confidence scores (JSONB format)

**ON DELETE Behavior**:
- ON DELETE CASCADE: Deleting a video recording deletes its transcript

**Quality Thresholds**:
- High Quality: confidence_score >= 0.80 (green indicator in admin UI)
- Medium Quality: 0.75 <= confidence_score < 0.80 (yellow indicator)
- Low Quality: confidence_score < 0.75 (red indicator, flag for manual review)

---

### 6. Menu

**Purpose**: Represents a restaurant menu that candidates review and provide feedback on.

**Fields**:
| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique menu identifier |
| name | VARCHAR(255) | NOT NULL, UNIQUE | Menu name (e.g., "Spring 2025 Menu", "Weekend Brunch") |
| description | TEXT | NULL | Optional menu description or theme |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE, INDEX | Whether menu is shown to candidates |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Menu creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |
| created_by_admin_id | UUID | FOREIGN KEY (admin_user.id) ON DELETE SET NULL, NULL | Admin who created the menu |

**Relationships**:
- One-to-many with MenuCategory (CASCADE on delete)
- Many-to-one with AdminUser (created_by_admin_id)

**Indexes**:
- `idx_menu_is_active` (is_active) - Filter active menus for candidate display
- `idx_menu_created_at` (created_at DESC) - Sort by creation date

**Validation Rules**:
- name must be non-empty and unique
- Only active menus (is_active = TRUE) are shown to candidates
- Admins can deactivate menus without deleting historical feedback

**ON DELETE Behavior**:
- ON DELETE CASCADE: Deleting a menu deletes all categories and dishes (use cautiously)
- created_by_admin_id ON DELETE SET NULL: Preserve menu if admin is deleted

---

### 7. MenuCategory

**Purpose**: Represents a section of a menu (e.g., appetizers, mains, desserts).

**Fields**:
| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique category identifier |
| menu_id | UUID | FOREIGN KEY (menu.id) ON DELETE CASCADE, NOT NULL, INDEX | Parent menu |
| category_name | VARCHAR(100) | NOT NULL | Category name (e.g., "Appetizers", "Entrees", "Desserts") |
| sequence_order | INTEGER | NOT NULL, INDEX | Display order within menu (1-indexed) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Category creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

**Relationships**:
- Many-to-one with Menu (menu_id)
- One-to-many with Dish (CASCADE on delete)

**Indexes**:
- `idx_category_menu_id` (menu_id, sequence_order) - Fast ordered retrieval
- `idx_category_sequence_order` (menu_id, sequence_order) - Unique constraint enforcement

**Unique Constraints**:
- `unique_menu_category_order` (menu_id, sequence_order) - Enforce ordered categories
- `unique_menu_category_name` (menu_id, category_name) - No duplicate category names per menu

**Validation Rules**:
- sequence_order must be positive integer (1, 2, 3, ...)
- category_name must be non-empty
- Admins can reorder categories (update sequence_order)

**ON DELETE Behavior**:
- ON DELETE CASCADE: Deleting a menu deletes all its categories

---

### 8. Dish

**Purpose**: Represents a menu item that candidates evaluate and provide feedback on.

**Fields**:
| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique dish identifier |
| category_id | UUID | FOREIGN KEY (menu_category.id) ON DELETE CASCADE, NOT NULL, INDEX | Parent category |
| dish_name | VARCHAR(255) | NOT NULL | Dish name (e.g., "Grilled Salmon", "Caesar Salad") |
| description | TEXT | NULL | Dish description or ingredients |
| photo_urls | TEXT[] | NULL | Array of S3 URLs for dish photos |
| price | DECIMAL(10,2) | NULL | Optional price for display |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE, INDEX | Whether dish is shown to candidates |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Dish creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

**Relationships**:
- Many-to-one with MenuCategory (category_id)
- One-to-many with Feedback (CASCADE on delete)
- One-to-many with ProposedDish (CASCADE on delete)

**Indexes**:
- `idx_dish_category_id` (category_id) - Fast lookup of category's dishes
- `idx_dish_is_active` (is_active) - Filter active dishes for candidate display
- `idx_dish_name` (dish_name) - Search by name

**Validation Rules**:
- dish_name must be non-empty
- photo_urls array can contain 0 to 5 URLs (PostgreSQL array field)
- price, if set, must be >= 0
- Only active dishes (is_active = TRUE) are shown to candidates

**ON DELETE Behavior**:
- ON DELETE CASCADE: Deleting a category deletes all its dishes

**PostgreSQL Array Field**:
- photo_urls uses TEXT[] array type for storing multiple image URLs
- Example: `{'https://s3.amazonaws.com/bucket/dish1.jpg', 'https://s3.amazonaws.com/bucket/dish2.jpg'}`

---

### 9. Feedback

**Purpose**: Stores candidate's evaluation of a dish (rating, comment, elimination vote).

**Fields**:
| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique feedback identifier |
| candidate_id | UUID | FOREIGN KEY (candidate.id) ON DELETE CASCADE, NOT NULL, INDEX | Candidate providing feedback |
| dish_id | UUID | FOREIGN KEY (dish.id) ON DELETE CASCADE, NOT NULL, INDEX | Dish being evaluated |
| rating | INTEGER | NULL, CHECK (rating >= 1 AND rating <= 5) | Star rating (1-5), NULL if not provided |
| comment_text | TEXT | NULL, CHECK (length(comment_text) <= 500) | Text comment (max 500 characters), NULL if not provided |
| should_eliminate | BOOLEAN | NOT NULL, DEFAULT FALSE | Vote to eliminate dish from menu |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Feedback submission timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

**Relationships**:
- Many-to-one with Candidate (candidate_id)
- Many-to-one with Dish (dish_id)
- One-to-many with ProposedDish (CASCADE on delete)

**Indexes**:
- `idx_feedback_candidate_id` (candidate_id) - Fast lookup of candidate's feedback
- `idx_feedback_dish_id` (dish_id) - Fast lookup of dish's feedback for aggregation
- `idx_feedback_rating` (dish_id, rating) - Filter by rating for analytics
- `idx_feedback_candidate_dish` (candidate_id, dish_id) - Unique constraint enforcement

**Unique Constraints**:
- `unique_candidate_dish_feedback` (candidate_id, dish_id) - Each candidate can provide only one feedback per dish

**Validation Rules**:
- rating, if provided, must be between 1 and 5
- comment_text, if provided, must be <= 500 characters
- should_eliminate defaults to FALSE
- **Partial Feedback Allowed**: rating and comment_text can both be NULL (candidate skipped this dish)
- At least one of (rating, comment_text, should_eliminate = TRUE) must be present to create feedback record
- Candidates can update feedback only when submission_status = 'incomplete'

**ON DELETE Behavior**:
- ON DELETE CASCADE: Deleting a candidate or dish deletes associated feedback

**Aggregation Queries** (see section below for SQL examples):
- Average rating per dish across all candidates
- Count of feedback entries per dish
- Count of elimination votes per dish
- Count of comments per dish

---

### 10. ProposedDish

**Purpose**: Stores candidate's alternative dish proposals with photos as replacements for existing dishes.

**Fields**:
| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique proposal identifier |
| feedback_id | UUID | FOREIGN KEY (feedback.id) ON DELETE CASCADE, NOT NULL, INDEX | Associated feedback record |
| candidate_id | UUID | FOREIGN KEY (candidate.id) ON DELETE CASCADE, NOT NULL, INDEX | Candidate proposing the dish |
| original_dish_id | UUID | FOREIGN KEY (dish.id) ON DELETE CASCADE, NOT NULL, INDEX | Dish being replaced |
| proposal_description | TEXT | NULL | Optional text description of proposed dish |
| photo_urls | TEXT[] | NOT NULL, CHECK (array_length(photo_urls, 1) <= 5) | Array of S3 URLs for proposed dish photos (max 5) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Proposal submission timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

**Relationships**:
- Many-to-one with Feedback (feedback_id)
- Many-to-one with Candidate (candidate_id)
- Many-to-one with Dish (original_dish_id)

**Indexes**:
- `idx_proposal_feedback_id` (feedback_id) - Fast lookup of proposals for feedback
- `idx_proposal_candidate_id` (candidate_id) - Fast lookup of candidate's proposals
- `idx_proposal_dish_id` (original_dish_id) - Fast lookup of proposals for a dish

**Validation Rules**:
- photo_urls array must contain 1 to 5 URLs (at least one photo required)
- Each photo must be <= 5 MB (enforced at API layer before S3 upload)
- Photo formats: 'image/jpeg', 'image/png', 'image/heic'
- Candidates can upload proposals only when submission_status = 'incomplete'

**ON DELETE Behavior**:
- ON DELETE CASCADE: Deleting feedback, candidate, or original dish deletes associated proposals

**PostgreSQL Array Field**:
- photo_urls uses TEXT[] array type for storing multiple image URLs
- Example: `{'https://s3.amazonaws.com/bucket/proposal1.jpg', 'https://s3.amazonaws.com/bucket/proposal2.jpg'}`

---

### 11. AdminUser

**Purpose**: Represents staff admin who reviews candidates and manages system (merged reviewer/admin role).

**Fields**:
| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique admin identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | Admin's email address for authentication |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hashed password |
| full_name | VARCHAR(255) | NOT NULL | Admin's full name |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE, INDEX | Whether admin can log in |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Admin account creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |
| last_login_at | TIMESTAMP | NULL | Timestamp of last successful login |

**Relationships**:
- One-to-many with AuditLog (SET NULL on delete)
- One-to-many with InterviewPrompt (created_by_admin_id, SET NULL on delete)
- One-to-many with Menu (created_by_admin_id, SET NULL on delete)

**Indexes**:
- `idx_admin_email` (email) - Fast lookup for authentication
- `idx_admin_is_active` (is_active) - Filter active admins

**Validation Rules**:
- Email must match regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- Password must be hashed with bcrypt (min 8 chars, uppercase, lowercase, number, symbol enforced at API layer)
- is_active = FALSE prevents login but preserves audit trail

**ON DELETE Behavior**:
- Related entities (InterviewPrompt, Menu, AuditLog) ON DELETE SET NULL to preserve historical records

**Permissions** (single admin role):
- View all candidates and submissions (read-only)
- Download documents, videos, transcripts
- Update candidate submission_status and final_decision
- Manage interview prompts (CRUD)
- Manage menus, categories, dishes (CRUD)
- View audit logs

---

### 12. AuditLog

**Purpose**: Records all admin actions accessing candidate data for compliance and security auditing.

**Fields**:
| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique log entry identifier |
| admin_user_id | UUID | FOREIGN KEY (admin_user.id) ON DELETE SET NULL, NULL, INDEX | Admin who performed the action |
| action_type | VARCHAR(100) | NOT NULL, INDEX | Action performed (see enum values below) |
| candidate_id | UUID | FOREIGN KEY (candidate.id) ON DELETE CASCADE, NULL, INDEX | Candidate whose data was accessed |
| resource_type | VARCHAR(50) | NULL | Type of resource accessed (Document, VideoRecording, etc.) |
| resource_id | UUID | NULL | ID of specific resource accessed |
| ip_address | INET | NULL | IP address of admin request |
| user_agent | TEXT | NULL | Browser/client user agent string |
| metadata | JSONB | NULL | Additional context (e.g., filters applied, search terms) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP, INDEX | Timestamp of action |

**Relationships**:
- Many-to-one with AdminUser (admin_user_id)
- Many-to-one with Candidate (candidate_id)

**Indexes**:
- `idx_audit_admin_id` (admin_user_id, created_at DESC) - View admin's action history
- `idx_audit_candidate_id` (candidate_id, created_at DESC) - View access history for candidate
- `idx_audit_action_type` (action_type, created_at DESC) - Filter by action type
- `idx_audit_created_at` (created_at DESC) - Recent actions

**Action Types** (action_type values):
- `VIEW_CANDIDATE_LIST` - Admin viewed candidate list
- `VIEW_CANDIDATE_DETAIL` - Admin viewed individual candidate page
- `DOWNLOAD_DOCUMENT` - Admin downloaded resume or cover letter
- `DOWNLOAD_TRANSCRIPT` - Admin downloaded video transcript
- `VIEW_VIDEO` - Admin played video recording
- `UPDATE_CANDIDATE_STATUS` - Admin changed submission_status
- `SET_FINAL_DECISION` - Admin set final_decision (eliminated/hired)
- `CREATE_INTERVIEW_PROMPT` - Admin created new prompt
- `UPDATE_INTERVIEW_PROMPT` - Admin edited prompt
- `DELETE_INTERVIEW_PROMPT` - Admin deleted prompt
- `CREATE_MENU` - Admin created new menu
- `UPDATE_MENU` - Admin edited menu
- `DELETE_MENU` - Admin deleted menu

**Validation Rules**:
- action_type must be one of the predefined values above
- candidate_id should be set for candidate-related actions
- created_at is immutable (audit logs cannot be modified or deleted)
- Logs are write-only; only admins with elevated permissions can view

**ON DELETE Behavior**:
- admin_user_id ON DELETE SET NULL: Preserve log if admin is deleted
- candidate_id ON DELETE CASCADE: Delete logs when candidate is deleted (per retention policy)

**Retention Policy**:
- Audit logs are retained for 90 days after candidate final_decision_at timestamp
- Logs for candidates without final_decision are retained indefinitely

---

## Aggregation Queries

### Admin Dashboard - Candidate List with Filters

**Query Pattern**: Fetch all candidates with counts of documents, videos, and feedback entries.

```sql
SELECT
    c.id,
    c.email,
    c.full_name,
    c.account_status,
    c.submission_status,
    c.final_decision,
    c.created_at,
    c.submitted_at,
    COUNT(DISTINCT d.id) AS document_count,
    COUNT(DISTINCT v.id) AS video_count,
    COUNT(DISTINCT f.id) AS feedback_count
FROM candidate c
LEFT JOIN document d ON c.id = d.candidate_id
LEFT JOIN video_recording v ON c.id = v.candidate_id
LEFT JOIN feedback f ON c.id = f.candidate_id
WHERE c.submission_status = 'submitted'  -- Filter example
GROUP BY c.id
ORDER BY c.submitted_at DESC
LIMIT 50 OFFSET 0;
```

**SQLAlchemy (Async) Example**:
```python
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

stmt = (
    select(
        Candidate.id,
        Candidate.email,
        Candidate.full_name,
        Candidate.account_status,
        Candidate.submission_status,
        Candidate.final_decision,
        Candidate.created_at,
        Candidate.submitted_at,
        func.count(func.distinct(Document.id)).label('document_count'),
        func.count(func.distinct(VideoRecording.id)).label('video_count'),
        func.count(func.distinct(Feedback.id)).label('feedback_count')
    )
    .outerjoin(Document, Candidate.id == Document.candidate_id)
    .outerjoin(VideoRecording, Candidate.id == VideoRecording.candidate_id)
    .outerjoin(Feedback, Candidate.id == Feedback.candidate_id)
    .where(Candidate.submission_status == 'submitted')
    .group_by(Candidate.id)
    .order_by(Candidate.submitted_at.desc())
    .limit(50)
    .offset(0)
)
result = await session.execute(stmt)
candidates = result.all()
```

---

### Gallery/Table View - Dish Feedback Aggregation

**Query Pattern**: Aggregate ratings, comment counts, elimination votes, and proposal counts per dish.

```sql
SELECT
    d.id AS dish_id,
    d.dish_name,
    mc.category_name,
    d.photo_urls[1] AS primary_photo_url,  -- First photo in array
    COUNT(DISTINCT f.id) AS feedback_count,
    ROUND(AVG(f.rating), 2) AS average_rating,
    COUNT(DISTINCT CASE WHEN f.comment_text IS NOT NULL THEN f.id END) AS comment_count,
    COUNT(DISTINCT CASE WHEN f.should_eliminate = TRUE THEN f.id END) AS elimination_vote_count,
    COUNT(DISTINCT p.id) AS proposal_count,
    ARRAY_AGG(DISTINCT c.full_name) FILTER (WHERE f.id IS NOT NULL) AS candidate_names
FROM dish d
JOIN menu_category mc ON d.category_id = mc.id
LEFT JOIN feedback f ON d.id = f.dish_id
LEFT JOIN candidate c ON f.candidate_id = c.id
LEFT JOIN proposed_dish p ON f.id = p.feedback_id
WHERE d.is_active = TRUE
    AND mc.category_name = 'Appetizers'  -- Filter example
GROUP BY d.id, mc.category_name
ORDER BY average_rating ASC NULLS LAST
LIMIT 50;
```

**SQLAlchemy (Async) Example**:
```python
from sqlalchemy import select, func, case

stmt = (
    select(
        Dish.id.label('dish_id'),
        Dish.dish_name,
        MenuCategory.category_name,
        Dish.photo_urls[0].label('primary_photo_url'),  # First photo
        func.count(func.distinct(Feedback.id)).label('feedback_count'),
        func.round(func.avg(Feedback.rating), 2).label('average_rating'),
        func.count(func.distinct(
            case((Feedback.comment_text.isnot(None), Feedback.id))
        )).label('comment_count'),
        func.count(func.distinct(
            case((Feedback.should_eliminate == True, Feedback.id))
        )).label('elimination_vote_count'),
        func.count(func.distinct(ProposedDish.id)).label('proposal_count'),
        func.array_agg(func.distinct(Candidate.full_name)).label('candidate_names')
    )
    .join(MenuCategory, Dish.category_id == MenuCategory.id)
    .outerjoin(Feedback, Dish.id == Feedback.dish_id)
    .outerjoin(Candidate, Feedback.candidate_id == Candidate.id)
    .outerjoin(ProposedDish, Feedback.id == ProposedDish.feedback_id)
    .where(Dish.is_active == True)
    .where(MenuCategory.category_name == 'Appetizers')
    .group_by(Dish.id, MenuCategory.category_name)
    .order_by(func.avg(Feedback.rating).asc().nullslast())
    .limit(50)
)
result = await session.execute(stmt)
dishes = result.all()
```

---

### Candidate Detail View - Complete Submission

**Query Pattern**: Fetch all candidate data (documents, videos, transcripts, feedback) in a single optimized query.

```sql
-- Candidate basic info
SELECT * FROM candidate WHERE id = :candidate_id;

-- Documents
SELECT * FROM document WHERE candidate_id = :candidate_id ORDER BY document_type;

-- Videos with transcripts
SELECT
    v.id,
    v.file_url,
    v.duration_seconds,
    v.transcription_status,
    ip.prompt_text,
    t.file_url AS transcript_url,
    t.confidence_score
FROM video_recording v
JOIN interview_prompt ip ON v.prompt_id = ip.id
LEFT JOIN transcript t ON v.id = t.video_recording_id
WHERE v.candidate_id = :candidate_id
ORDER BY ip.sequence_order;

-- Feedback with dishes and proposals
SELECT
    f.id,
    d.dish_name,
    mc.category_name,
    f.rating,
    f.comment_text,
    f.should_eliminate,
    COALESCE(
        ARRAY_AGG(p.photo_urls) FILTER (WHERE p.id IS NOT NULL),
        ARRAY[]::TEXT[][]
    ) AS proposal_photo_urls
FROM feedback f
JOIN dish d ON f.dish_id = d.id
JOIN menu_category mc ON d.category_id = mc.id
LEFT JOIN proposed_dish p ON f.id = p.feedback_id
WHERE f.candidate_id = :candidate_id
GROUP BY f.id, d.dish_name, mc.category_name
ORDER BY mc.sequence_order, d.dish_name;
```

---

### Admin Analytics - Transcription Quality Report

**Query Pattern**: Find low-quality transcripts requiring manual review.

```sql
SELECT
    c.full_name AS candidate_name,
    c.email,
    ip.prompt_text,
    t.confidence_score,
    v.file_url AS video_url,
    t.file_url AS transcript_url,
    v.created_at AS upload_date
FROM transcript t
JOIN video_recording v ON t.video_recording_id = v.id
JOIN candidate c ON v.candidate_id = c.id
JOIN interview_prompt ip ON v.prompt_id = ip.id
WHERE t.confidence_score < 0.75
ORDER BY t.confidence_score ASC
LIMIT 100;
```

---

## Database Indexes Strategy

### Primary Indexes (Automatic)

All primary keys are indexed automatically by PostgreSQL.

### Foreign Key Indexes (Required)

**Rationale**: Foreign keys are frequently used in JOINs and WHERE clauses. Indexing them improves join performance and referential integrity checks.

- `idx_document_candidate_id` ON document(candidate_id)
- `idx_video_candidate_id` ON video_recording(candidate_id)
- `idx_video_prompt_id` ON video_recording(prompt_id)
- `idx_transcript_video_recording_id` ON transcript(video_recording_id)
- `idx_category_menu_id` ON menu_category(menu_id)
- `idx_dish_category_id` ON dish(category_id)
- `idx_feedback_candidate_id` ON feedback(candidate_id)
- `idx_feedback_dish_id` ON feedback(dish_id)
- `idx_proposal_feedback_id` ON proposed_dish(feedback_id)
- `idx_proposal_candidate_id` ON proposed_dish(candidate_id)
- `idx_proposal_dish_id` ON proposed_dish(original_dish_id)
- `idx_audit_admin_id` ON audit_log(admin_user_id)
- `idx_audit_candidate_id` ON audit_log(candidate_id)

### Query Pattern Indexes

**Rationale**: These indexes optimize frequent query patterns identified in the spec.

**Candidate List Filtering** (Admin Dashboard):
- `idx_candidate_submission_status` ON candidate(submission_status)
- `idx_candidate_account_status` ON candidate(account_status)
- `idx_candidate_created_at` ON candidate(created_at DESC)
- `idx_candidate_email` ON candidate(email) -- Authentication

**Transcription Job Queue** (ARQ Worker):
- `idx_video_transcription_status` ON video_recording(transcription_status, created_at)

**Gallery/Table View Aggregation**:
- `idx_dish_is_active` ON dish(is_active)
- `idx_feedback_rating` ON feedback(dish_id, rating) -- Average rating calculation
- `idx_transcript_confidence_score` ON transcript(confidence_score) -- Low-quality flagging

**Audit Trail Queries**:
- `idx_audit_action_type` ON audit_log(action_type, created_at DESC)
- `idx_audit_created_at` ON audit_log(created_at DESC)

**Menu/Category Ordering**:
- `idx_prompt_sequence_order` ON interview_prompt(sequence_order)
- `idx_category_sequence_order` ON menu_category(menu_id, sequence_order)
- `idx_menu_is_active` ON menu(is_active)

### Unique Constraints (Implicit Indexes)

**Rationale**: Unique constraints automatically create indexes for enforcement.

- `unique_candidate_email` ON candidate(email)
- `unique_admin_email` ON admin_user(email)
- `unique_candidate_document_type` ON document(candidate_id, document_type)
- `unique_candidate_prompt_response` ON video_recording(candidate_id, prompt_id)
- `unique_candidate_dish_feedback` ON feedback(candidate_id, dish_id)
- `unique_menu_category_order` ON menu_category(menu_id, sequence_order)
- `unique_menu_category_name` ON menu_category(menu_id, category_name)
- `unique_prompt_sequence_order` ON interview_prompt(sequence_order)

### Composite Indexes

**Rationale**: Optimize multi-column queries and aggregations.

- `idx_category_menu_sequence` ON menu_category(menu_id, sequence_order) -- Ordered category retrieval
- `idx_feedback_candidate_dish` ON feedback(candidate_id, dish_id) -- Unique constraint + lookup
- `idx_audit_admin_created` ON audit_log(admin_user_id, created_at DESC) -- Admin action history
- `idx_audit_candidate_created` ON audit_log(candidate_id, created_at DESC) -- Candidate access history

### Index Maintenance Notes

- **Partial Indexes**: Consider adding partial indexes for active-only records if inactive records grow significantly:
  ```sql
  CREATE INDEX idx_dish_active_only ON dish(category_id) WHERE is_active = TRUE;
  CREATE INDEX idx_menu_active_only ON menu(id) WHERE is_active = TRUE;
  ```

- **JSONB Indexes**: If querying provider_metadata in Transcript frequently, add GIN index:
  ```sql
  CREATE INDEX idx_transcript_metadata ON transcript USING GIN(provider_metadata);
  ```

- **Full-Text Search**: If searching candidate names or dish descriptions, add tsvector indexes:
  ```sql
  CREATE INDEX idx_candidate_name_fts ON candidate USING GIN(to_tsvector('english', full_name));
  CREATE INDEX idx_dish_name_fts ON dish USING GIN(to_tsvector('english', dish_name));
  ```

---

## State Management & Transitions

### Candidate Lifecycle

```
┌─────────────┐
│  unverified │ (account_status)
└──────┬──────┘
       │ email verification
       ▼
┌─────────────┐
│    active   │
└──────┬──────┘
       │ (can be suspended by admin)
       ▼
┌─────────────┐
│  suspended  │ (optional admin action)
└─────────────┘

Submission Flow (submission_status):
┌──────────────┐
│  incomplete  │ (initial state)
└──────┬───────┘
       │ candidate final submission
       ▼
┌──────────────┐
│   submitted  │
└──────┬───────┘
       │ admin begins review
       ▼
┌──────────────┐
│ under_review │
└──────┬───────┘
       │ admin completes review
       ▼
┌──────────────┐
│   reviewed   │
└──────┬───────┘
       │ admin makes final decision
       ▼
┌──────────────┐ ┌──────────────┐
│  eliminated  │ │    hired     │ (final_decision)
└──────────────┘ └──────────────┘
```

### VideoRecording Transcription Lifecycle

```
┌─────────────┐
│   pending   │ (initial state after upload)
└──────┬──────┘
       │ ARQ job picks up video
       ▼
┌─────────────┐
│ processing  │
└──────┬──────┘
       │
       ├────────► ┌─────────────┐
       │          │  completed  │ (success)
       │          └─────────────┘
       │
       ├────────► ┌─────────────┐
       │          │   failed    │ (retry eligible)
       │          └──────┬──────┘
       │                 │ retry with exponential backoff
       │                 └──────► (back to processing)
       │
       └────────► ┌─────────────┐
                  │ unavailable │ (max retries exceeded or service down)
                  └─────────────┘
```

**Graceful Degradation**:
- If transcription status is `failed` or `unavailable`, candidate can still submit
- Admin sees "Transcription Unavailable" badge in UI
- Admin can still play video directly without transcript

---

## Data Integrity Rules

### Immutability Constraints

**Rationale**: Prevent data tampering after submission to ensure audit trail integrity.

1. **Candidate Submissions**: Once `submission_status` transitions from `incomplete` to `submitted`:
   - No updates allowed to Document, VideoRecording, Feedback, ProposedDish
   - Enforced at API layer with 403 Forbidden response

2. **Audit Logs**: AuditLog records are write-only:
   - No UPDATE or DELETE operations allowed
   - Enforced at database level with trigger (optional) or API layer

3. **Transcript Integrity**: Transcript records cannot be modified after creation:
   - Only INSERT allowed; UPDATE/DELETE restricted
   - If transcription must be regenerated, create new Transcript record and mark old one as superseded

### Cascade Deletion Rules

**Safe Cascades** (data cleanup):
- Candidate → Document, VideoRecording, Feedback, ProposedDish, AuditLog (CASCADE)
- Menu → MenuCategory → Dish → Feedback, ProposedDish (CASCADE, use cautiously)
- Feedback → ProposedDish (CASCADE)
- VideoRecording → Transcript (CASCADE)

**Protected Cascades** (preserve historical data):
- InterviewPrompt → VideoRecording (RESTRICT: cannot delete prompts with responses)
- AdminUser → InterviewPrompt, Menu, AuditLog (SET NULL: preserve records if admin deleted)

### Referential Integrity

All foreign keys enforce referential integrity:
- `ON DELETE CASCADE`: Automatically delete dependent records
- `ON DELETE RESTRICT`: Prevent deletion if dependent records exist
- `ON DELETE SET NULL`: Preserve record but clear foreign key reference

---

## JSON Field Schemas

### Transcript.provider_metadata (JSONB)

**Purpose**: Store provider-specific transcription data for advanced features.

**Example Schema (AssemblyAI)**:
```json
{
  "provider": "assemblyai",
  "transcript_id": "5551722-f677-48ae-a23d-f801b3c2e888",
  "audio_duration": 178.5,
  "words": [
    {
      "text": "Hello",
      "start": 1250,
      "end": 1580,
      "confidence": 0.98
    },
    {
      "text": "I'm",
      "start": 1580,
      "end": 1820,
      "confidence": 0.95
    }
  ],
  "language_code": "en_us",
  "language_confidence": 0.97
}
```

**Queryable Fields** (with GIN index):
- Extract language: `provider_metadata->>'language_code'`
- Filter by confidence: `(provider_metadata->>'language_confidence')::numeric > 0.9`

---

### AuditLog.metadata (JSONB)

**Purpose**: Store contextual information for admin actions.

**Example Schemas**:

**VIEW_CANDIDATE_LIST**:
```json
{
  "filters": {
    "submission_status": ["submitted", "under_review"],
    "created_after": "2025-01-01"
  },
  "sort": "submitted_at DESC",
  "page": 2,
  "limit": 50
}
```

**DOWNLOAD_TRANSCRIPT**:
```json
{
  "transcript_id": "uuid-here",
  "file_name": "Why do you want to work in our test kitchen - Jane Smith.txt",
  "download_url_expires_at": "2025-11-13T15:30:00Z"
}
```

**SET_FINAL_DECISION**:
```json
{
  "previous_decision": null,
  "new_decision": "hired",
  "notes": "Excellent menu feedback and creative proposals"
}
```

---

## Partial Feedback Handling

**Clarification**: Candidates can skip dishes without providing ratings or comments (FR-032).

**Implementation**:
1. **No Feedback Record**: If candidate skips a dish entirely, no Feedback record is created
2. **Partial Feedback Record**: If candidate provides at least one of (rating, comment, should_eliminate = TRUE), create Feedback record with NULL values for unprovided fields

**Query Pattern** (Identify dishes without feedback from a candidate):
```sql
-- Find dishes candidate has NOT provided feedback on
SELECT d.id, d.dish_name
FROM dish d
WHERE d.id NOT IN (
    SELECT dish_id FROM feedback WHERE candidate_id = :candidate_id
);
```

**Admin Analytics** (Dish coverage across candidates):
```sql
-- Count how many candidates reviewed each dish
SELECT
    d.dish_name,
    COUNT(DISTINCT f.candidate_id) AS candidate_count,
    (SELECT COUNT(*) FROM candidate WHERE submission_status = 'submitted') AS total_candidates,
    ROUND(
        COUNT(DISTINCT f.candidate_id)::numeric /
        (SELECT COUNT(*) FROM candidate WHERE submission_status = 'submitted')::numeric * 100,
        2
    ) AS coverage_percentage
FROM dish d
LEFT JOIN feedback f ON d.id = f.dish_id
GROUP BY d.id
ORDER BY coverage_percentage DESC;
```

---

## Migration Strategy

### Phase 1: Core Entities (MVP)
1. Create tables: AdminUser, Candidate, InterviewPrompt, Menu, MenuCategory, Dish
2. Add authentication and basic admin CRUD functionality
3. Test candidate account creation and email verification

### Phase 2: Media Entities
1. Create tables: Document, VideoRecording, Transcript
2. Implement S3 upload and transcription pipeline
3. Test video wizard flow end-to-end

### Phase 3: Feedback Entities
1. Create tables: Feedback, ProposedDish
2. Implement menu review and aggregation queries
3. Test gallery/table view toggle

### Phase 4: Audit & Analytics
1. Create table: AuditLog
2. Implement middleware for action logging
3. Build admin analytics views

### Rollback Strategy
- Use Alembic migrations with downgrade scripts
- Test migrations on staging database before production
- Keep data dumps before major schema changes

---

## Performance Considerations

### Expected Data Volume (per spec assumptions)
- **Candidates**: 50-100 concurrent per hiring cycle
- **Videos**: 3-5 per candidate × 100 candidates = 300-500 videos
- **Dishes**: ~15-25 per menu
- **Feedback**: 15-25 per candidate × 100 candidates = 1,500-2,500 records
- **Audit Logs**: ~50 actions per candidate review × 100 candidates = 5,000 records per cycle

### Optimization Strategies
1. **Pagination**: Limit queries to 50 results with OFFSET for large lists
2. **Eager Loading**: Use SQLAlchemy `selectinload()` for N+1 query prevention
3. **Database Aggregation**: Compute averages/counts in PostgreSQL, not application layer
4. **Connection Pooling**: Configure asyncpg pool size (min=5, max=20)
5. **Caching**: Cache menu data (rarely changes) in Redis with 1-hour TTL

### Query Performance Targets (per spec SC-008 to SC-010)
- Candidate list (100+ candidates): < 3 seconds
- Gallery view (50+ dishes): < 2 seconds
- Table view sorting/filtering (500+ dishes): < 1 second
- Achieved through proper indexing and database-level aggregation

---

## Security Considerations

### Encryption
- **At Rest**: Enable PostgreSQL encryption for entire database (vendor-managed keys)
- **In Transit**: Enforce SSL/TLS connections (require `sslmode=require` in connection string)
- **Application Layer**: Use bcrypt for password hashing (cost factor 12)

### Access Control
- **Row-Level Security**: Candidates can only query their own data (enforced at API layer)
- **Admin Permissions**: Admins have read-only access to candidate data (no UPDATE/DELETE)
- **Role-Based Middleware**: FastAPI dependency injection validates JWT claims

### Data Retention
- **Active Candidates**: Retain indefinitely until final_decision is made
- **Post-Decision**: Retain for 90 days after final_decision_at
- **Audit Logs**: Retain for 90 days after candidate deletion
- **Automated Cleanup**: Scheduled cron job for retention policy enforcement

### PII Protection
- **Sensitive Fields**: email, phone, full_name (candidate and admin)
- **Access Logging**: All PII access logged in AuditLog (FR-006, FR-055)
- **Export Restrictions**: Bulk export disabled; individual downloads only

---

## Appendix: SQLAlchemy Model Examples

### Candidate Model

```python
from sqlalchemy import Column, String, Enum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
import uuid

class AccountStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    ACTIVE = "active"
    SUSPENDED = "suspended"

class SubmissionStatus(str, enum.Enum):
    INCOMPLETE = "incomplete"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    REVIEWED = "reviewed"

class FinalDecision(str, enum.Enum):
    ELIMINATED = "eliminated"
    HIRED = "hired"

class Candidate(Base):
    __tablename__ = "candidate"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    account_status = Column(
        Enum(AccountStatus),
        nullable=False,
        default=AccountStatus.UNVERIFIED,
        index=True
    )
    submission_status = Column(
        Enum(SubmissionStatus),
        nullable=False,
        default=SubmissionStatus.INCOMPLETE,
        index=True
    )
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    final_decision = Column(Enum(FinalDecision), nullable=True)
    final_decision_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    documents = relationship("Document", back_populates="candidate", cascade="all, delete-orphan")
    videos = relationship("VideoRecording", back_populates="candidate", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="candidate", cascade="all, delete-orphan")
    proposals = relationship("ProposedDish", back_populates="candidate", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="candidate", cascade="all, delete-orphan")
```

### Feedback Model (with partial data support)

```python
from sqlalchemy import Column, Integer, Text, Boolean, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidate.id", ondelete="CASCADE"), nullable=False, index=True)
    dish_id = Column(UUID(as_uuid=True), ForeignKey("dish.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=True)  # NULL allowed for partial feedback
    comment_text = Column(Text, nullable=True)  # NULL allowed for partial feedback
    should_eliminate = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    candidate = relationship("Candidate", back_populates="feedback")
    dish = relationship("Dish", back_populates="feedback")
    proposals = relationship("ProposedDish", back_populates="feedback", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("rating IS NULL OR (rating >= 1 AND rating <= 5)", name="check_rating_range"),
        CheckConstraint("length(comment_text) <= 500", name="check_comment_length"),
        UniqueConstraint("candidate_id", "dish_id", name="unique_candidate_dish_feedback"),
    )
```

---

## Summary

This data model provides a complete, production-ready schema for the Chef Candidate Evaluation Platform with:

- **11 core entities** covering candidates, documents, videos, transcripts, menus, feedback, and admin users
- **UUID primary keys** for distributed system compatibility
- **Comprehensive indexing strategy** optimized for admin dashboard and analytics queries
- **State management** for candidate lifecycle and transcription processing
- **Audit trail** logging all admin actions accessing candidate data
- **Partial feedback support** allowing candidates to skip dishes
- **Graceful degradation** for transcription failures
- **Immutability guarantees** for submitted data
- **PostgreSQL-specific features** (JSONB, array fields, INET type)
- **SQLAlchemy 2.0 compatibility** with async support

The schema is designed to support the MVP requirements (FR-001 to FR-056) while maintaining data integrity, security, and performance at scale (50-100 concurrent candidates per hiring cycle).
