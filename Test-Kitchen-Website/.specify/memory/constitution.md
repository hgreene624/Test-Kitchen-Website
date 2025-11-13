<!--
Sync Impact Report:
- Version change: (new constitution) → 1.0.0
- Rationale: Initial constitution for Test Kitchen / Menu Development Chef Interview Site
- Modified principles: N/A (initial creation)
- Added sections: All sections (initial creation)
- Removed sections: N/A
- Templates requiring updates:
  ✅ plan-template.md: Constitution Check section aligns with principles
  ✅ spec-template.md: Requirements structure supports constitution mandates
  ✅ tasks-template.md: Task categorization reflects principle-driven development
- Follow-up TODOs: None
-->

# Test Kitchen / Menu Development Chef Interview Site Constitution

## Core Principles

### I. User Role Separation (NON-NEGOTIABLE)

The system MUST maintain strict separation between candidate and administrative roles with distinct authentication flows, data access boundaries, and permission models.

**Rules:**
- Candidates MUST ONLY access their own submission data, video recordings, and feedback
- Admin/reviewer roles MUST have read-only access to candidate data by default; write access limited to explicit review actions (ratings, comments, elimination votes)
- Role-based access control (RBAC) MUST be enforced at API/service layer, NOT just UI layer
- Authentication tokens/sessions MUST include role claims; middleware MUST validate role on every protected route
- Cross-role data leakage (e.g., candidate seeing other candidates' submissions) MUST be prevented by design

**Rationale:** Candidate screening involves sensitive personal data and competitive evaluation. Privacy violations or data leakage would undermine trust and potentially violate employment law requirements.

### II. Media & Data Integrity

All video/audio recordings, transcripts, menu photos, ratings, comments, and proposals MUST be stored with immutability guarantees, audit trails, and secure access controls.

**Rules:**
- Video/audio recordings MUST be uploaded to secure storage with encryption at rest
- Once submitted, candidate media MUST NOT be deletable by candidate; only admin can remove for compliance reasons (with audit log)
- Transcripts generated from recordings MUST be versioned; if re-transcribed, original version MUST be retained
- All ratings, comments, proposals, and elimination votes MUST be timestamped and attributed to specific reviewer user ID
- Menu photos MUST be stored with metadata (upload timestamp, candidate ID, menu section association)
- Aggregated feedback (e.g., average ratings, comment counts) MUST be computed on-demand or cached with invalidation strategy, NOT stored as source of truth

**Rationale:** Interview process requires traceability and auditability. Immutable media records prevent disputes; audit trails support fairness reviews and compliance checks.

### III. Sequential Candidate Experience (NON-NEGOTIABLE)

Candidate-facing UI MUST follow a low-friction, linear wizard flow that guides candidates step-by-step through interview stages without overwhelming navigation or dead-ends.

**Rules:**
- Wizard flow MUST present one task per screen/step: (1) Upload basic info → (2) Record video answer(s) → (3) Review menu with photos → (4) Submit ratings/comments/proposals
- Progress indicator MUST show current step and total steps; candidate MUST be able to navigate backward to review/edit prior steps before final submission
- Mobile-first design: wizard MUST be fully usable on smartphone (portrait orientation); desktop is secondary concern
- No candidate-facing dashboard or complex navigation; single "continue" or "next" button per step
- Error states MUST provide clear, actionable guidance (e.g., "Video recording failed: check microphone permission" with retry button)

**Rationale:** Candidates are under evaluation stress; cognitive load must be minimized. Linear flow reduces confusion and abandonment rates, especially on mobile devices where navigation chrome is expensive.

### IV. Admin/Reviewer Gallery & Table Toggle

Staff-facing UI MUST provide two viewing modes for candidate submissions: (1) visual gallery for rapid menu photo review, (2) sortable/filterable table for data-driven comparison.

**Rules:**
- Gallery mode MUST display menu photos in grid layout with overlay showing candidate name, dish name, rating summary (if available)
- Table mode MUST support sorting by candidate name, submission date, average rating, reviewer completion status; filtering by menu section, rating range, elimination status
- Toggle between modes MUST preserve current filter/sort state (user doesn't lose context when switching views)
- Both modes MUST link to candidate detail page showing full submission (video, transcript, photos, all ratings/comments/proposals from all reviewers)
- Mobile: gallery mode is primary; table mode may require horizontal scroll or card-based responsive alternative

**Rationale:** Different review tasks require different views. Gallery mode supports rapid visual assessment of menu aesthetics; table mode supports analytical comparison and consensus-building discussions.

### V. Modularity & Independent Evolution

System architecture MUST decompose into distinct modules (authentication, recording, menu-review, feedback, AI-analysis, admin-dashboard) that can be developed, tested, and updated independently.

**Rules:**
- Each module MUST expose clear interfaces (API contracts) with versioned endpoints or function signatures
- Module interdependencies MUST be documented in design artifacts (data-model.md, contracts/)
- Changes to one module MUST NOT break other modules unless interface contract changes (which MUST be flagged as breaking change requiring cross-module coordination)
- Shared domain entities (Candidate, Menu, Dish, Feedback, Reviewer) MUST have canonical data models defined in data-model.md; modules reference these models but do NOT own them
- Testing: each module MUST have unit tests for internal logic; integration tests for cross-module interactions

**Rationale:** Prototype needs agility. Modular architecture allows parallel development (e.g., one developer works on recording module while another works on AI-analysis module) and isolated bug fixes without regression risk.

### VI. Test-First for Critical Flows (NON-NEGOTIABLE)

Video recording, menu photo upload, and feedback submission flows MUST follow test-first discipline: write failing tests, get user approval, then implement.

**Rules:**
- **Critical flows:** Candidate video recording (capture, upload, playback verification), menu photo upload (multiple images, size/format validation), feedback submission (rating/comment persistence, proposal attachment)
- For each critical flow: write contract test (API endpoint behavior) and integration test (end-to-end user journey) BEFORE implementation
- Tests MUST fail before code is written; tests MUST pass after implementation
- UI tests (automated browser tests or manual test checklists) MUST cover wizard navigation, gallery/table toggle, and error states
- Non-critical flows (e.g., admin user management, transcript re-generation) MAY use test-after approach if time-constrained, but MUST still have test coverage before release

**Rationale:** Recording and upload failures are high-impact user experience problems. Test-first discipline catches edge cases (poor network, unsupported formats, concurrent submissions) early and prevents production firefighting.

### VII. AI Integration Transparency & Human Review

AI-powered transcript analysis and candidate recommendation features MUST be auditable, explainable, and subject to human reviewer override; AI outputs MUST NOT auto-eliminate candidates.

**Rules:**
- Transcript analysis (e.g., keyword extraction, sentiment scoring, competency mapping) MUST log: prompt used, model/version, timestamp, raw response
- AI recommendations (e.g., "best fit for pastry role based on transcript") MUST show reasoning (which transcript excerpts, which scoring factors contributed)
- Reviewers MUST be able to view AI analysis summary alongside candidate submission BUT retain full authority to rate/comment independently
- Elimination votes MUST be human reviewer actions; AI MAY flag candidates for reviewer attention (e.g., "low engagement detected in video") but MUST NOT auto-reject
- AI prompts and analysis logic MUST be version-controlled; changes to prompts MUST be documented in design artifacts

**Rationale:** AI evaluation carries bias risk and opacity concerns. Transparency requirements support fairness audits and compliance with employment law (e.g., EEOC guidance on algorithmic hiring tools). Human-in-the-loop design maintains accountability.

### VIII. Performance for Media & Aggregations

System MUST handle video uploads (up to 5 minutes, ~100 MB), menu photo galleries (20-50 images per candidate), and feedback aggregation (10+ reviewers rating 50+ candidates) without user-perceptible latency.

**Rules:**
- Video upload MUST support chunked/resumable upload; progress indicator MUST show upload percentage
- Video transcription MAY be asynchronous (background job); candidate sees "processing" state; reviewer sees transcript when ready
- Menu photo galleries MUST use lazy loading or pagination if >20 images; thumbnails MUST be optimized (<100 KB each)
- Aggregated feedback (average ratings, comment counts) MUST compute in <2 seconds for up to 100 candidates × 10 reviewers; use database aggregation queries or caching strategy
- Page load time for gallery/table views MUST be <3 seconds on desktop broadband; <5 seconds on mobile 4G

**Rationale:** Media-heavy workflows are sensitive to performance degradation. Poor upload experience causes candidate frustration; slow admin dashboard causes reviewer abandonment.

### IX. Security, Privacy & Minimal Retention

Personal data (candidate names, contact info, video/audio) MUST be encrypted at rest and in transit; access MUST be logged; data MUST be retained only as long as legally required for hiring process.

**Rules:**
- Video/audio MUST be stored in encrypted blob storage (e.g., S3 with SSE, Azure Blob with encryption)
- API endpoints MUST use HTTPS/TLS 1.2+; session tokens MUST be HTTP-only, Secure, SameSite cookies or JWT with short expiration
- All access to candidate personal data (PII) and media MUST be logged with user ID, timestamp, action (view/download/rate)
- Data retention policy MUST be configurable (default: 90 days post-hiring decision); admin MUST be able to bulk-delete candidate data after retention period
- Candidate MUST be able to request data deletion (right to be forgotten) unless legal hold applies; deletion MUST be logged

**Rationale:** Candidate data includes sensitive personal information and employment evaluation records. Security failures risk legal liability (GDPR, CCPA, state employment laws). Minimal retention reduces risk surface.

### X. Simplicity & Prototype-Friendliness

System MUST prioritize simplicity over enterprise patterns; lightweight backends (e.g., serverless functions, Firebase, Google Sheets for config) and minimal dependencies are PREFERRED over heavy frameworks.

**Rules:**
- For MVP: prefer managed services (Auth0/Firebase Auth, S3/Cloudinary for media, serverless functions for API) over self-hosted infrastructure
- Database MAY start as JSON files or Google Sheets for configuration data (e.g., menu sections, dish templates) if structured data <1000 rows
- Avoid premature abstraction: no repository pattern, no ORM, no complex dependency injection UNLESS complexity justified in plan.md Complexity Tracking table
- Frontend MUST use modern, simple framework (e.g., Next.js, SvelteKit) with minimal build configuration; avoid custom webpack configs
- Codebase MUST have clear README with "Quick Start" section: install dependencies → set environment variables → run dev server (3 steps max)

**Rationale:** This is a prototype for a specific hiring workflow, not a general-purpose platform. Over-engineering adds maintenance burden and slows iteration. Simplicity enables faster feature delivery and easier onboarding for new developers.

## Data & Media Governance

### Storage & Access

- **Video/audio recordings:** Encrypted blob storage with signed URLs for time-limited access; candidates and reviewers access via signed URLs (no direct S3/blob keys exposed)
- **Transcripts:** Stored as text with foreign key to recording; versioned if re-transcribed
- **Menu photos:** Organized by candidate ID and menu section; metadata includes upload timestamp, file size, MIME type
- **Ratings/comments/proposals:** Relational data (SQL) or document store (Firestore/MongoDB) with foreign keys to candidate, reviewer, dish; MUST support aggregation queries
- **Aggregated feedback:** Computed views or cached results; MUST invalidate when new ratings/comments added

### Data Lineage & Audit

- Every candidate submission (video, photos, ratings) MUST be traceable to specific candidate ID and submission timestamp
- Every reviewer action (rating, comment, elimination vote) MUST be traceable to specific reviewer user ID and timestamp
- AI analysis runs MUST log prompt, model version, input data references (transcript ID), output data (summary, scores)
- Admin actions (data deletion, role changes, export) MUST be logged to audit trail (separate table/log stream)

## UI/UX Mandates

### Candidate Wizard Flow

1. **Step 1: Basic Info** – Name, email, phone (optional), upload resume (optional)
2. **Step 2: Video Interview** – Record video answer to prompt(s); playback verification; re-record option
3. **Step 3: Menu Review** – View menu photos grouped by section (appetizers, mains, desserts); navigate with swipe/arrow
4. **Step 4: Feedback** – Rate each dish (1-5 stars); add text comments; upload proposal photos (optional)
5. **Step 5: Review & Submit** – Summary page showing all inputs; edit links back to prior steps; final "Submit Application" button

**Design constraints:**
- Mobile-first: large touch targets (min 44×44 px); minimal text entry (prefer sliders, star ratings, checkboxes)
- Single column layout; no sidebars or split views
- Clear "Save Draft" option at each step (data persists in browser local storage or backend draft record)
- Loading states for video upload / transcription with progress indicators

### Admin/Reviewer Dashboard

1. **Landing Page: Candidate List** – Table or gallery view with toggle; filter by status (pending, reviewed, eliminated, hired)
2. **Candidate Detail Page** – Video player, transcript panel, menu photo gallery, ratings/comments from all reviewers, AI analysis summary (if available)
3. **Review Action Panel** – Rate each dish (1-5 stars); add comments; submit proposal photos; mark candidate as eliminated (with confirmation prompt); export aggregated feedback to PDF/CSV

**Design constraints:**
- Desktop-first: table view supports sorting, multi-column filters
- Gallery view: grid layout with 3-4 columns on desktop; 2 columns on tablet; 1 column on mobile
- Responsive: no horizontal scroll on mobile (table switches to card layout or vertical stack)

## Testing & Quality Standards

### Test Coverage Requirements

- **Unit tests:** All business logic (rating calculations, filtering/sorting functions, data transformations) MUST have unit tests with >80% line coverage
- **Integration tests:** All API endpoints (candidate submission, reviewer feedback, AI analysis trigger) MUST have contract tests verifying request/response schema and error codes
- **UI tests:** Wizard flow (all 5 steps) and gallery/table toggle MUST have automated browser tests (Playwright/Cypress) or documented manual test checklists
- **Performance tests:** Video upload (100 MB file), photo gallery load (50 images), feedback aggregation (50 candidates × 10 reviewers) MUST be load-tested with documented results in plan.md

### Quality Gates

- All tests MUST pass before merging to main branch
- No critical security vulnerabilities (OWASP Top 10) in dependencies
- Lighthouse score for candidate wizard: Performance >70, Accessibility >90
- Admin dashboard table view: page load <3 seconds for 100 candidates

## AI Integration Governance

### Transcript Analysis

- Transcription service: use managed API (e.g., AWS Transcribe, Google Speech-to-Text, AssemblyAI) with confidence scores logged
- Analysis prompts: version-controlled in codebase or design docs; changes MUST be reviewed and documented
- Analysis outputs: structured JSON with reasoning field; stored with reference to source transcript and prompt version
- Human review: AI summaries displayed alongside transcript; reviewers can flag inaccurate analysis; flagged cases logged for prompt tuning

### Candidate Recommendation

- Recommendation algorithm: documented in design artifacts (e.g., weighted scoring based on video keywords, dish ratings, proposal creativity scores)
- Explainability: MUST show which factors contributed to recommendation score (e.g., "Video mentioned 'seasonal' 8 times; 4.5 avg rating on desserts")
- No auto-elimination: AI MAY rank candidates but MUST NOT automatically reject; human reviewer makes final decision

### Auditability

- Every AI analysis run MUST log: user who triggered analysis, candidate ID, timestamp, model/version, prompt hash, output summary
- Audit log MUST be exportable for compliance review
- Reviewers MUST be able to re-run analysis (e.g., if prompt updated or model upgraded) with new results stored separately (original results retained)

## Performance & Scalability

### Expected Scale

- **MVP:** 10-50 candidates, 3-5 reviewers, 5-20 dishes per menu
- **Growth:** 100-500 candidates, 10-20 reviewers, 20-50 dishes per menu

### Performance Targets

- **Video upload:** Support 5-minute videos (~100 MB); chunked upload with resume capability; completion within 2 minutes on broadband
- **Transcription:** Asynchronous processing; 5-minute video transcribed within 10 minutes
- **Photo gallery:** Load 50 thumbnails (optimized to <100 KB each) within 3 seconds
- **Feedback aggregation:** Compute average ratings for 100 candidates × 10 reviewers × 20 dishes within 2 seconds
- **Dashboard page load:** <3 seconds for table view with 100 rows; <2 seconds for gallery view with 50 candidates

### Scalability Strategy

- **Horizontal scaling:** API backend MUST be stateless (use external session store or JWT); can scale across multiple instances
- **Media storage:** Use CDN or edge caching for menu photos; signed URLs for video with short expiration
- **Database:** Use indexes on candidate ID, reviewer ID, submission timestamp, rating scores; consider read replicas if >1000 candidates
- **Async processing:** Video transcription and AI analysis MUST run as background jobs (queue-based: SQS, Cloud Tasks, Celery)

## Security, Privacy & Compliance

### Authentication & Authorization

- **Candidates:** Email/password or magic link (passwordless); email verification required before submission
- **Reviewers/admins:** SSO (Google Workspace, Okta) or username/password with MFA; role assignment managed by admin
- **Session management:** JWT with 1-hour expiration and refresh token rotation OR server-side sessions with 24-hour timeout
- **Password policy:** Min 8 characters, complexity requirements (uppercase, lowercase, number, symbol); hashed with bcrypt or Argon2

### Data Protection

- **Encryption at rest:** All PII and media files encrypted (AES-256); managed service encryption acceptable (S3 SSE, database TDE)
- **Encryption in transit:** HTTPS/TLS 1.2+ for all API calls; no plain HTTP endpoints
- **Access logging:** All PII access (view candidate profile, download video) logged with user ID, timestamp, IP address
- **Data exports:** Aggregated feedback exports MUST NOT include PII unless reviewer has explicit admin permission; exports logged

### Privacy & Retention

- **Data minimization:** Collect only data necessary for evaluation (no social security numbers, birth dates, full addresses)
- **Consent:** Candidates MUST acknowledge consent to recording and evaluation before starting interview
- **Retention policy:** Candidate data retained for 90 days post-hiring decision (configurable); automated deletion job runs monthly
- **Right to deletion:** Candidates can request data deletion via email to admin; admin processes request within 30 days (logged)

### Compliance

- **GDPR (if EU candidates):** Right to access, right to deletion, data portability, consent withdrawal
- **CCPA (if California candidates):** Right to know, right to deletion, opt-out of sale (N/A for hiring)
- **Employment law:** No discriminatory bias in AI evaluation; audit trail for fairness review; interview questions must comply with EEOC guidance

## Schema & Contract Clarity

### Domain Entities (High-Level)

Detailed schemas MUST be defined in `data-model.md`. Constitution mandates these entities exist:

- **Candidate:** ID, name, email, submission timestamp, status (draft, submitted, reviewed, eliminated, hired)
- **VideoRecording:** ID, candidate ID, file URL, duration, upload timestamp, transcript ID (nullable), transcription status
- **Transcript:** ID, recording ID, text content, confidence score, generated timestamp, model version
- **Menu:** ID, name, description (e.g., "Spring 2025 Menu")
- **Dish:** ID, menu ID, section (appetizer, main, dessert, etc.), name, description, photo URLs (array)
- **Feedback:** ID, candidate ID, reviewer ID, dish ID (nullable if general feedback), rating (1-5), comment text, proposal photo URLs, timestamp
- **Reviewer:** ID, name, email, role (reviewer, admin), hire date
- **AIAnalysis:** ID, transcript ID, prompt version, model version, summary text, structured scores (JSON), generated timestamp

### API Contracts

Detailed endpoints MUST be defined in `contracts/` directory. Constitution mandates these contract types:

- **Candidate submission endpoints:** POST /candidates, POST /recordings, POST /feedback
- **Reviewer endpoints:** GET /candidates, GET /candidates/:id, POST /candidates/:id/feedback, POST /candidates/:id/eliminate
- **AI analysis endpoints:** POST /transcripts/:id/analyze, GET /analysis/:id
- **Admin endpoints:** GET /reviewers, POST /reviewers, DELETE /candidates/:id (data deletion)

## Simplicity & Extensibility

### Simplicity Rules

- **Avoid over-engineering:** No microservices for MVP; monolithic API acceptable if <5000 LOC
- **Minimal dependencies:** Use framework-included batteries (Next.js API routes, Django ORM, Rails ActiveRecord) before adding ORMs or custom abstractions
- **Configuration over code:** Menu sections, dish templates, interview prompts stored in config files or Google Sheets; no hard-coded strings in business logic
- **README-driven:** Every module MUST have README with purpose, dependencies, and quickstart

### Extensibility Rules

- **New roles:** Admin MUST be able to add new reviewer roles (e.g., "head chef", "sous chef") with different permission sets
- **New menu sections:** Admin MUST be able to add new menu sections (e.g., "brunch", "beverages") without code changes (config-driven)
- **New feedback types:** System SHOULD support adding new feedback fields (e.g., "plating creativity score") via configuration, not code rewrite
- **New AI features:** AI analysis prompts and outputs MUST be modular; adding new analysis types (e.g., "voice tone analysis") MUST NOT require refactoring existing analysis code

## Reviewability & Audit

### Audit Trail Requirements

- **Candidate actions:** Submit application, upload video, submit feedback – logged with timestamp
- **Reviewer actions:** View candidate, rate dish, add comment, eliminate candidate – logged with user ID and timestamp
- **Admin actions:** Create reviewer, delete candidate data, export feedback – logged with user ID, timestamp, and affected entity IDs
- **AI actions:** Transcript generated, analysis run – logged with model version, prompt version, and output reference

### Audit Log Access

- Admin MUST be able to view audit logs via dashboard (filterable by user, action type, date range)
- Audit logs MUST be exportable to CSV for compliance review
- Audit logs MUST be retained for minimum 1 year (configurable)

### Data Lineage Visibility

- Candidate detail page MUST show timeline of all actions (submission → transcription → reviews → elimination/hire decision)
- Reviewer dashboard MUST show which reviewers have completed reviews for each candidate
- AI analysis summary MUST show which transcript version, prompt version, and model version generated results

## Code Style & Collaboration

### Naming Conventions

- **Variables/functions:** camelCase (JavaScript/TypeScript) or snake_case (Python)
- **Classes/types:** PascalCase
- **Constants:** UPPER_SNAKE_CASE
- **Files:** kebab-case for source files (e.g., `candidate-service.ts`, `feedback-controller.py`)
- **Directories:** lowercase with hyphens (e.g., `admin-dashboard/`, `api-routes/`)

### Modular Architecture

- **Separation of concerns:** Business logic in services; API routes thin (validation + service call); UI components presentational (props in, events out)
- **Dependency direction:** UI depends on API contracts; services depend on data models; no circular dependencies
- **Shared code:** Extract common utilities (date formatting, validation helpers) to `utils/` or `lib/` directory

### Documentation Requirements

- **README.md:** Quick start (install, configure, run), architecture overview, link to detailed docs
- **data-model.md:** Entity schemas with field types, constraints, relationships
- **contracts/*.md:** API endpoint specs with request/response examples and error codes
- **plan.md:** Technical context, constitution check, project structure, complexity justification
- **Code comments:** Business logic functions MUST have docstrings explaining purpose, parameters, return values; no obvious comments (e.g., `// increment counter` for `counter++`)

### Collaboration Workflow

- **Branching:** Feature branches from main; branch name format `###-feature-name` (e.g., `001-video-recording`, `002-menu-review`)
- **Pull requests:** MUST reference feature spec; MUST include test coverage summary; MUST pass CI checks before merge
- **Code review:** At least one reviewer approval required; reviewers check: (1) constitution compliance, (2) test coverage, (3) API contract adherence, (4) code clarity
- **Commits:** Descriptive commit messages (e.g., "Add candidate video upload endpoint with validation"); squash commits before merge if >10 commits per feature

## Governance

### Amendment Procedure

1. **Proposal:** Any team member MAY propose amendment by creating issue/doc with rationale and impact analysis
2. **Review:** Team reviews proposal; identifies affected templates (plan, spec, tasks) and existing features
3. **Approval:** Simple majority vote (or BDFL decision if single-developer project)
4. **Migration:** Update constitution, bump version (semantic versioning), update dependent templates and documentation
5. **Communication:** Announce amendment in team channel/README changelog; affected in-progress features MUST update plan.md to reflect new rules

### Versioning Policy

- **MAJOR (X.0.0):** Backward-incompatible principle removal or redefinition (e.g., removing "Test-First" requirement, changing role separation model)
- **MINOR (0.X.0):** New principle added, new governance section, material expansion of existing principle (e.g., adding "Performance Monitoring" principle)
- **PATCH (0.0.X):** Clarifications, wording improvements, typo fixes, non-semantic updates

### Compliance Review

- **Per-feature:** Every feature plan.md MUST include "Constitution Check" section verifying compliance with all principles
- **Quarterly:** Team reviews codebase against constitution; documents violations and remediation plan
- **Pre-release:** Final constitution check before production deployment; any violations MUST be justified in release notes or fixed before release

### Enforcement

- This constitution supersedes all other coding guidelines, style guides, and unwritten practices
- Pull requests MAY be rejected solely on grounds of constitution violation, even if code is functionally correct
- Complexity MUST be justified: any abstraction, pattern, or dependency not mandated by constitution MUST be explained in plan.md Complexity Tracking table
- Use `.specify/` templates and commands for all feature planning and implementation to ensure constitution alignment

**Version**: 1.0.0 | **Ratified**: 2025-11-13 | **Last Amended**: 2025-11-13
