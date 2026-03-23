# Technology Research: Chef Candidate Evaluation Platform

**Date**: 2025-11-13
**Purpose**: Resolve technology selection decisions for implementation plan

---

## 1. Frontend Framework Selection

**Decision**: Next.js 15 (React with App Router)

**Rationale**: Next.js provides the best balance of prototype-friendly development, extensive ecosystem support, and production-grade capabilities for this MVP. The React ecosystem offers mature video recording libraries (react-media-recorder), battle-tested UI component libraries (shadcn/ui + Tailwind CSS for responsive grids/tables), and robust form management (React Hook Form for multi-step wizards). While SvelteKit offers superior bundle sizes, Next.js's larger ecosystem, comprehensive documentation, and zero-config deployment to Vercel make it the safest choice for rapid MVP development with minimal friction.

**Alternatives Considered**:
- **SvelteKit**: Rejected despite excellent performance (60-80% smaller bundles) and gentle learning curve due to smaller ecosystem—fewer ready-made solutions for video recording, limited UI component libraries, and smaller developer community means more custom implementation work for a prototype.
- **Nuxt 3 (Vue)**: Rejected because Vue's ecosystem, while mature, has fewer specialized libraries for MediaRecorder integration and video handling compared to React, and the learning curve is comparable to Next.js without providing significant prototype-speed advantages.
- **Vanilla HTML+JS**: Rejected because manual implementation of wizard state management, form validation, responsive layouts, and video upload progress would require 3-4x development time compared to framework-based solutions.

**Implementation Notes**:
- **Video Recording**: Use `react-media-recorder` or implement custom hook with MediaRecorder API; use 'use client' directive for Next.js App Router
- **Responsive Grids/Tables**: Use shadcn/ui Table + Data Table components with Tailwind CSS (`grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4` for gallery)
- **Wizard Flow**: React Hook Form with multi-step pattern or rhf-wizard library; supports validation per step and backward navigation
- **Upload Progress**: Native XMLHttpRequest progress events or tus-js-client for resumable uploads
- **Deployment**: Zero-config to Vercel with automatic framework detection

---

## 2. Backend Framework Selection

**Decision**: FastAPI (Python)

**Rationale**: FastAPI is the optimal choice for this prototype MVP because it provides native async/await support with seamless integration to battle-tested job queue systems (Celery or ARQ) for fire-and-forget video transcription, excellent file upload handling through streaming multipart parsing, and SQLAlchemy ORM with async PostgreSQL support. The framework's automatic OpenAPI documentation, Pydantic validation, and straightforward deployment options (Railway, Render, Docker) make it ideal for rapid MVP development while maintaining production-grade async job processing capabilities.

**Alternatives Considered**:
- **Next.js API routes**: Rejected due to serverless limitations (10-second execution timeout on Vercel, 5MB payload limit for 100MB videos, requires external services for background jobs)
- **Express.js (Node.js)**: Rejected because ecosystem requires assembling multiple libraries (Multer/Busboy, Prisma/Drizzle, Passport), resulting in more integration work compared to FastAPI's batteries-included approach
- **Django + DRF**: Rejected due to heavier framework overhead unsuitable for MVP velocity; FastAPI provides equivalent functionality with less boilerplate and better async performance

**Implementation Notes**:
- **Async Job Library**: ARQ (Async Redis Queue) for MVP; migrate to Celery if job complexity increases
- **File Upload**: FastAPI's streaming multipart parser with `request.stream()` or streaming-form-data library; integrate with S3 multipart upload API
- **ORM**: SQLAlchemy 2.0 with async support, asyncpg driver for PostgreSQL, optional SQLModel for Pydantic integration
- **Project Structure**:
  ```
  backend/app/
  ├── main.py
  ├── config.py
  ├── api/v1/ (auth.py, candidates.py, admin.py, media.py)
  ├── models/ (SQLAlchemy models)
  ├── schemas/ (Pydantic request/response)
  ├── services/ (business logic)
  ├── workers/ (ARQ/Celery tasks)
  └── middleware/
  ```
- **Deployment**: Railway.app (auto-deploy from GitHub, built-in PostgreSQL and Redis, web + worker services)

---

## 3. Database Selection

**Decision**: PostgreSQL

**Rationale**: PostgreSQL is the standard choice for relational data with complex queries (feedback aggregation, sorting/filtering). It provides:
- Excellent aggregation performance for admin dashboard queries
- ACID guarantees for data integrity (immutable submissions, audit logs)
- JSON field support for flexible data (e.g., proposed dish metadata)
- Mature ecosystem with SQLAlchemy async support
- Managed service availability (Railway, Render, AWS RDS, Supabase)

**Alternatives Considered**:
- **SQLite**: Suitable for local development only; no concurrent write support for production
- **Firestore/MongoDB**: NoSQL not ideal for relational queries (candidates → feedback → dishes); aggregation queries less efficient
- **MySQL**: Comparable to PostgreSQL but slightly weaker JSON support and async driver ecosystem

**Implementation Notes**:
- Use asyncpg driver for Python (faster than psycopg)
- Create indexes on: candidate_id, dish_id, submission_status, created_at
- Use database-level aggregation queries for admin gallery/table views
- Leverage PostgreSQL array fields for photo URLs (multiple images per proposal)

---

## 4. Blob Storage for Media

**Decision**: Local Filesystem on VPS

**Rationale**: For Hostinger VPS deployment, local filesystem storage is the simplest and most cost-effective solution for MVP phase. No external service costs, no API rate limits, direct file access for serving media, and sufficient for expected scale (50-100 candidates, ~10-50GB storage). Files organized in dedicated storage directory with separate folders for media types. Can migrate to S3-compatible storage (MinIO, Backblaze B2) later if needed.

**Alternatives Considered**:
- **AWS S3**: Rejected; requires AWS account, external costs (~$15-20/month), additional complexity for VPS deployment
- **Self-hosted MinIO on VPS**: Rejected for MVP; adds 2-4GB RAM overhead, additional service to maintain, unnecessary complexity for current scale
- **Cloudinary**: Rejected due to 100MB video limit on free tier and $89/month Plus plan cost
- **Backblaze B2 / Wasabi**: Rejected for MVP; external costs ($5-6/TB/month), API complexity, can migrate later if scale demands

**Implementation Notes**:
- **Storage Path**: `/var/www/chef-candidate-media/` on VPS with subdirectories: `videos/`, `documents/`, `photos/`
- **File Organization**: Organize by type and candidate ID (e.g., `videos/{candidate_id}/{video_id}.mp4`)
- **Permissions**: Nginx user must have read access; FastAPI process needs read/write access
- **Chunked Upload**: Use FastAPI's `UploadFile` with streaming to disk; track progress in-memory or via Redis
- **File Serving**: Nginx serves static files directly (fast) or FastAPI generates secure file paths with path validation
- **Backup Strategy**: Regular rsync or tar backups to separate VPS volume or external backup service
- **Security**:
  - Files stored outside web root to prevent direct access
  - FastAPI validates file access permissions (candidate can only access own files)
  - Nginx location block for authenticated file serving
- **Migration Path**: If scale requires, can switch to MinIO (install on VPS) or external S3-compatible service (Backblaze B2) with minimal code changes

---

## 5. Video Transcription Service

**Decision**: AssemblyAI

**Rationale**: AssemblyAI offers superior accuracy (6% WER), excellent async API with SDK-managed polling, $50 free credits covering entire prototype phase (~8,100 minutes = 1,620 5-minute videos), and only $15.42 for 500 videos if credits exhausted. Turnaround time averages <1 minute per 5-minute video (well under <10 minute requirement). Word-level confidence scores enable quality assessment (flag transcripts with <75% avg confidence per spec clarification).

**Alternatives Considered**:
- **AWS Transcribe**: Rejected; 4x more expensive ($60 vs $15.42 for 2,500 minutes), less generous free tier
- **Google Speech-to-Text**: Rejected; more expensive than AssemblyAI, 24-hour batch turnaround may not meet <10 min requirement
- **Deepgram**: Rejected; lower accuracy (9.3% WER) despite faster speed and generous free credit
- **OpenAI Whisper (self-hosted)**: Rejected; infrastructure costs and processing time (2x real-time) impractical for prototype

**Implementation Notes**:
- **SDK**: `assemblyai` package (Python) or npm package (JavaScript)
- **Async Polling**: Use `.transcribe()` for blocking with auto-polling (3s interval) or webhook pattern for production
- **Confidence Scores**: Word-level scores (0.0-1.0); flag transcripts with avg <0.75 as low quality
- **File Naming**: `{prompt_text} - {candidate_name}.txt` per spec FR-019
- **Error Handling**: Graceful degradation per clarification; mark as "unavailable", allow admin to view video without transcript, implement retry with exponential backoff
- **Cost**: $0 for prototype (covered by $50 free credit)

---

## 6. Authentication Strategy

**Decision**: Custom Authentication (bcrypt + JWT)

**Rationale**: Per clarification, authentication is basic only (email verification + password complexity, no password reset, no account lockout, no MFA). Custom implementation with bcrypt for password hashing and JWT for session tokens is simplest and avoids vendor lock-in or monthly costs. FastAPI + Pydantic make custom auth straightforward with minimal boilerplate.

**Alternatives Considered**:
- **Auth0**: Rejected; overkill for basic auth requirements, monthly costs ($25/month for 1K users), adds external dependency
- **Firebase Auth**: Rejected; similar to Auth0, monthly costs and vendor lock-in for simple use case
- **Supabase Auth**: Rejected; while free tier is generous, adds complexity for basic email/password flow

**Implementation Notes**:
- **Password Hashing**: bcrypt with `passlib[bcrypt]` library (Python)
- **Session Tokens**: JWT with `python-jose[cryptography]`; include role claim (candidate/admin) for RBAC
- **Email Verification**: Generate verification token, send email with link, verify token on callback
- **Middleware**: FastAPI dependency injection for role-based route protection
- **Session Management**: JWT with 24-hour expiration (no refresh tokens for MVP)

---

## 7. Video Recording in Browser

**Decision**: MediaRecorder API with WebM (VP8/VP9) and MP4 (H.264) Fallback

**Rationale**: MediaRecorder API is supported in Chrome, Safari 14.1+, Firefox, and Edge. WebM is the default format for Chrome/Firefox; Safari requires MP4. Use feature detection to select appropriate MIME type per browser.

**Implementation Notes**:
- **MediaRecorder API**: Use `react-media-recorder` wrapper or custom hook
- **Format Detection**:
  ```javascript
  const mimeType = MediaRecorder.isTypeSupported('video/webm; codecs=vp9')
    ? 'video/webm; codecs=vp9'
    : MediaRecorder.isTypeSupported('video/webm; codecs=vp8')
    ? 'video/webm; codecs=vp8'
    : 'video/mp4'; // Safari fallback
  ```
- **Constraints**: `{ video: { width: 1280, height: 720 }, audio: true }`
- **Recording UI**: Start/stop buttons, playback preview, re-record option, timer display (max 5 minutes)
- **Error Handling**: Clear messages for camera permission denied, storage full, unsupported format

---

## 8. Chunked/Resumable Upload Implementation

**Decision**: AWS S3 Multipart Upload with tus Protocol (Optional Enhancement)

**Rationale**: S3's native multipart upload API supports chunking large files (>100MB) with progress tracking. For MVP, use AWS SDK's `Upload` class which handles chunking automatically. For enhanced resume capability (survive browser refresh), consider tus protocol with tus-js-client as future enhancement.

**Implementation Notes**:
- **MVP Approach**: AWS SDK v3 `Upload` class with `httpUploadProgress` events
  ```javascript
  import { Upload } from "@aws-sdk/lib-storage";
  const upload = new Upload({
    client: s3Client,
    params: { Bucket: "bucket", Key: "video.mp4", Body: file }
  });
  upload.on("httpUploadProgress", (progress) => {
    const percent = (progress.loaded / progress.total) * 100;
    // Update UI progress bar
  });
  await upload.done();
  ```
- **Enhanced (Future)**: tus-js-client for true resumable uploads (stores upload state in browser local storage)
- **Chunk Size**: 5MB default (S3 minimum); increase to 10MB for faster uploads on good connections
- **Error Handling**: Retry failed chunks automatically (built into SDK); show retry button on final failure

---

## Summary of Technology Stack

| Component | Technology | Version/Details |
|-----------|-----------|-----------------|
| **Frontend** | Next.js (React) | v15 with App Router, Tailwind CSS, shadcn/ui |
| **Backend** | FastAPI (Python) | Latest with async support |
| **Database** | PostgreSQL | Latest with asyncpg driver |
| **Job Queue** | ARQ (Redis) | Async Redis Queue for transcription jobs |
| **Blob Storage** | AWS S3 | Standard tier with SSE-S3 encryption |
| **Transcription** | AssemblyAI | Async API with $50 free credit |
| **Authentication** | Custom (bcrypt + JWT) | python-jose, passlib |
| **ORM** | SQLAlchemy 2.0 | Async support with asyncpg |
| **Video Recording** | MediaRecorder API | react-media-recorder wrapper |
| **File Upload** | S3 Multipart Upload | AWS SDK v3 Upload class |
| **Deployment** | Railway.app | Web + worker services, managed PostgreSQL/Redis |

**Total Estimated Monthly Cost (Prototype)**:
- Storage: $0-20 (free tier covers initial testing)
- Transcription: $0 (covered by $50 free credit)
- Database: $0 (Railway free tier)
- Deployment: $0-5 (Railway Hobby plan)
- **Total**: ~$0-25/month

---

## Next Steps

1. Update `plan.md` Technical Context section with resolved technology choices
2. Proceed to Phase 1: Data Model & API Contracts design
3. Generate `data-model.md` with entity schemas
4. Generate API contract specifications in `contracts/` directory
5. Create `quickstart.md` for local development setup
