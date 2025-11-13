# REST API Contract Specifications

**Project**: Chef Candidate Evaluation Platform
**Technology Stack**: FastAPI (Python) with Pydantic schemas
**Created**: 2025-11-13
**Status**: Design Phase - Ready for Implementation

---

## Overview

This directory contains comprehensive REST API contract specifications for the Chef Candidate Evaluation Platform. Each contract file defines endpoints, request/response schemas, business rules, error handling, and mappings to functional requirements.

---

## Contract Files

### 1. [auth-api.md](./auth-api.md) - Authentication & Authorization
**Base URL**: `/api/v1/auth`
**Endpoints**: 7 endpoints
**Scope**: User signup, login, logout, email verification, session management

**Key Features**:
- JWT token-based authentication (1-hour expiry)
- Role-based access control (candidate vs admin)
- Email verification workflow
- Password complexity validation (8+ chars, uppercase, lowercase, number, symbol)
- Admin account creation (admin-only)

**Referenced FRs**: FR-001 to FR-006

---

### 2. [candidate-api.md](./candidate-api.md) - Candidate Submission Workflows
**Base URL**: `/api/v1/candidates`
**Endpoints**: 12 endpoints
**Scope**: Document uploads, video recordings, menu feedback, final submission

**Key Features**:
- Document upload (resume, cover letter) with format validation (PDF, DOC, DOCX)
- Video recording submission with re-record capability
- Interview prompt retrieval for wizard flow
- Menu and dish listing with categories
- Dish feedback (ratings, comments, elimination votes, proposed dishes)
- Auto-save feedback during menu review
- Final submission with completeness validation

**Referenced FRs**: FR-005, FR-007 to FR-017, FR-023 to FR-032, FR-053, FR-054

---

### 3. [admin-api.md](./admin-api.md) - Admin Review & Management
**Base URL**: `/api/v1/admin`
**Endpoints**: 12 endpoints
**Scope**: Candidate review, dish feedback analysis, interview prompt management

**Key Features**:
- Paginated candidate list with filtering (status, search) and sorting
- Complete candidate detail view (documents, videos, transcripts, feedback)
- Transcript download with formatted filenames
- Candidate status updates (reviewed, eliminated, hired)
- Gallery and table views for dish feedback aggregation
- Dish detail with all candidate feedback
- Interview prompt CRUD operations (add, edit, remove, reorder)
- Audit logging for all admin actions

**Referenced FRs**: FR-006, FR-033 to FR-052, FR-055

---

### 4. [media-api.md](./media-api.md) - Media Upload & Access
**Base URL**: `/api/v1/media`
**Endpoints**: 6 endpoints
**Scope**: Chunked/resumable uploads, signed URL access, storage management

**Key Features**:
- Chunked upload initiation (5 MB chunks recommended)
- Chunk upload with progress tracking and integrity verification
- Upload finalization with automatic transcription trigger
- Resumable upload support (check status, resume after interruption)
- Signed URL generation for secure file access (1-hour expiry)
- File deletion (pre-submission for candidates, anytime for admins)
- Support for videos (100 MB max), documents (10 MB max), photos (5 MB max)

**Referenced FRs**: FR-005, FR-006, FR-008, FR-010, FR-015, FR-031, FR-036, FR-037, FR-054, FR-056

---

### 5. [transcription-api.md](./transcription-api.md) - Async Transcription Processing
**Base URL**: `/api/v1/transcriptions`
**Endpoints**: 6 endpoints + 1 webhook
**Scope**: Asynchronous video-to-text transcription with job management

**Key Features**:
- Automatic transcription job creation after video upload
- Job status polling (pending, processing, completed, failed, unavailable)
- Transcript retrieval with word-level timing and confidence scores
- Formatted transcript files: "[Prompt Text] - [Candidate Name].txt"
- Graceful degradation (failed transcription doesn't block candidate submission)
- Retry mechanism for failed jobs (max 3 attempts)
- Webhook callback support for third-party transcription services
- Multi-service support (AWS Transcribe, AssemblyAI, Google Speech-to-Text, etc.)

**Referenced FRs**: FR-005, FR-006, FR-018 to FR-022, FR-038

---

## Common Patterns

### Authentication
All protected endpoints require:
```
Authorization: Bearer {jwt_token}
```

### Error Response Format
```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "additional context"
  }
}
```

### Pagination (List Endpoints)
```
?page=1&page_size=20&sort_by=created_at&sort_order=desc
```

Response includes:
```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 100,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  }
}
```

### Signed URLs
- Default expiry: 1 hour (3600 seconds)
- Maximum expiry: 24 hours (configurable)
- Regenerated on each request
- Used for: documents, videos, photos, transcripts

### File Upload Validation
- **Videos**: WebM, MP4 | Max 100 MB | Max 5 minutes
- **Documents**: PDF, DOC, DOCX | Max 10 MB
- **Photos**: JPG, PNG, HEIC | Max 5 MB

---

## HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST (resource created) |
| 400 | Bad Request | Validation errors, invalid input |
| 401 | Unauthorized | Invalid/expired token, authentication required |
| 403 | Forbidden | Insufficient permissions (role/ownership check failed) |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource (e.g., email already exists) |
| 413 | Payload Too Large | Request body exceeds size limit |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | External service (e.g., transcription) unavailable |

---

## Role-Based Access Control

### Candidate Role
- Can only access own data (documents, videos, feedback)
- Cannot view other candidates' submissions
- Cannot access admin endpoints
- Cannot modify data after final submission

### Admin Role
- Can access all candidate data
- Can update candidate status (reviewed, eliminated, hired)
- Can manage interview prompts
- Can view aggregated feedback across candidates
- All actions logged to audit trail

---

## Data Integrity & Audit

**Immutability** (FR-054):
- Candidates cannot delete/edit submissions after final submission
- Historical prompt responses preserved even if prompts are deleted/modified

**Audit Logging** (FR-055, FR-056):
- All admin access to candidate data logged
- Admin actions logged (status updates, prompt changes, file downloads)
- Logs include: admin ID, timestamp, action type, resource ID
- 90-day data retention (configurable)

**Encryption** (FR-010):
- All media files stored with encryption at rest
- Secure signed URLs for temporary access
- TLS/HTTPS for data in transit

---

## Implementation Checklist

- [ ] Set up FastAPI project structure
- [ ] Define Pydantic schemas for all request/response models
- [ ] Implement JWT authentication middleware
- [ ] Create role-based access control decorators
- [ ] Set up S3-compatible storage (or local filesystem for dev)
- [ ] Integrate chunked/resumable upload library
- [ ] Configure transcription service API client
- [ ] Implement background task queue (Celery/RQ) for async jobs
- [ ] Add input validation and error handling
- [ ] Create API documentation (auto-generated via FastAPI Swagger/ReDoc)
- [ ] Write contract tests for each endpoint
- [ ] Set up audit logging middleware
- [ ] Configure CORS for frontend integration
- [ ] Add rate limiting middleware
- [ ] Deploy to staging environment

---

## Testing Strategy

**Contract Tests**:
- Validate request/response schemas match Pydantic models
- Test all error responses (400, 401, 403, 404, 500)
- Verify HTTP status codes

**Integration Tests**:
- End-to-end candidate submission flow
- Admin review workflow
- Resumable upload with interruption/resume
- Transcription job lifecycle (trigger → poll → retrieve)

**Security Tests**:
- Authentication bypass attempts
- Role escalation attempts (candidate accessing admin endpoints)
- Cross-candidate data access attempts
- Token expiration and refresh

---

## Next Steps

1. **Review contracts** with stakeholders and frontend team
2. **Generate tasks** using `/speckit.tasks` command
3. **Implement Phase 1**: Authentication + basic CRUD endpoints
4. **Implement Phase 2**: Media upload + resumable upload flow
5. **Implement Phase 3**: Async transcription + job management
6. **Implement Phase 4**: Admin dashboard + aggregation queries
7. **Integration testing** with frontend
8. **Performance testing** (upload speed, dashboard load time)
9. **Security audit** (penetration testing, OWASP compliance)
10. **Deploy to production**

---

## Questions or Feedback?

These contracts are living documents and will evolve during implementation. If you find inconsistencies, missing edge cases, or areas for improvement, please update the relevant contract file and document the change in the git commit message.

**Contact**: [Your Team Contact Info]
**Last Updated**: 2025-11-13
