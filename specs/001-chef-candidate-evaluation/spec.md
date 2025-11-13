# Feature Specification: Chef Candidate Evaluation Platform

**Feature Branch**: `001-chef-candidate-evaluation`
**Created**: 2025-11-13
**Status**: Draft
**Input**: Build a password-protected web application to evaluate chef candidates for menu-development and test-kitchen roles.

## Clarifications

### Session 2025-11-13

- Q: How should the system handle authentication security beyond basic password complexity? → A: Basic only: password complexity rules, email verification (current spec coverage)
- Q: What are the permission differences between "Reviewer" and "Admin" roles mentioned in the AdminUser entity? → A: Merge into single role, admin. Admin will review
- Q: Must candidates provide feedback (rating/comment) on ALL dishes in the menu, or can they skip dishes? → A: Optional: candidates can skip dishes; submission allowed with partial feedback
- Q: When the transcription service fails or is unavailable, how should the system behave? → A: Graceful degradation: candidate proceeds; video stored; admin sees "transcription unavailable"; manual review possible
- Q: What operational metrics and monitoring should the system provide for admins to ensure healthy operation? → A: None: rely on application logs only; no dashboard metrics

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Candidate Account Creation and Profile Setup (Priority: P1)

A prospective chef candidate discovers the application and needs to create an account and submit their basic credentials before beginning the interview process.

**Why this priority**: This is the entry point for all candidates. Without account creation and credential upload, no other candidate features are accessible. This is the foundation for the entire candidate journey.

**Independent Test**: Can be fully tested by creating an account, logging in, and uploading resume and cover letter. Delivers value by capturing candidate contact information and initial credentials for admin review.

**Acceptance Scenarios**:

1. **Given** a new visitor arrives at the application, **When** they click "Sign Up" and provide email and password, **Then** their account is created and they receive email verification
2. **Given** a verified candidate logs in for the first time, **When** they are prompted to upload resume and cover letter, **Then** they can select and upload both documents (PDF, DOC, DOCX formats) and see upload confirmation
3. **Given** a candidate has uploaded their documents, **When** they view their profile, **Then** they can see their uploaded documents and re-upload if needed before starting the interview

---

### User Story 2 - Video Interview Recording (Priority: P1)

A candidate progresses through a sequential wizard where they record video responses to interview prompts, with the ability to review and re-record before submission.

**Why this priority**: The video interview is the core evaluation mechanism for assessing candidate communication skills, culinary knowledge, and personality. This is critical for the screening process.

**Independent Test**: Can be tested independently by presenting interview prompts, recording video responses, and verifying video playback and submission. Delivers value by capturing candidate video responses for admin evaluation.

**Acceptance Scenarios**:

1. **Given** a candidate has completed profile setup, **When** they enter the video interview wizard, **Then** they see the first interview prompt with camera permission request and recording controls
2. **Given** a candidate is viewing an interview prompt, **When** they record a video response (up to 5 minutes), **Then** they can review the recording, re-record if unsatisfied, and confirm to proceed to the next prompt
3. **Given** a candidate has recorded responses to all prompts, **When** they complete the video interview section, **Then** videos are uploaded with progress indicators and automatic transcript generation begins
4. **Given** a candidate's video has been uploaded, **When** transcription completes, **Then** the transcript is labeled with the prompt text and candidate name (e.g., "Why do you want to work in our test kitchen - Jane Smith.txt")

---

### User Story 3 - Menu Review and Feedback Submission (Priority: P1)

A candidate reviews restaurant menus organized by category, views dish photos and details, and provides feedback through ratings, comments, elimination votes, and dish proposals.

**Why this priority**: This feature evaluates the candidate's culinary judgment, creativity, and critical thinking about menu development. Essential for assessing fit for menu-development and test-kitchen roles.

**Independent Test**: Can be tested by displaying menus with photos, collecting ratings/comments/votes, and capturing proposed new dishes. Delivers value by gathering candidate's menu evaluation feedback.

**Acceptance Scenarios**:

1. **Given** a candidate has completed video interviews, **When** they enter the menu review section, **Then** they see menus organized by category (appetizers, mains, desserts, etc.) with dish photos, names, and descriptions
2. **Given** a candidate is viewing a dish, **When** they provide feedback, **Then** they can rate the dish 1-5 stars, add text comments, vote to eliminate the dish, and optionally upload photos of proposed alternative dishes
3. **Given** a candidate has reviewed multiple dishes, **When** they navigate between categories, **Then** their feedback is auto-saved and they can return to edit before final submission
4. **Given** a candidate has completed all menu reviews, **When** they submit their feedback, **Then** they see a confirmation summary of their ratings, comments, and proposals

---

### User Story 4 - Admin View of Candidate Submissions (Priority: P2)

Admins can view all candidate submissions including uploaded documents, video recordings, transcripts, and per-dish feedback in a comprehensive candidate detail view.

**Why this priority**: Admins need to review candidate materials to make hiring decisions. This provides the complete candidate evaluation interface.

**Independent Test**: Can be tested by displaying all candidate data (uploads, videos, transcripts, feedback) in a single view. Delivers value by enabling admin review and decision-making.

**Acceptance Scenarios**:

1. **Given** an admin logs into the system, **When** they view the candidate list, **Then** they see all candidates with submission status (incomplete, pending review, reviewed, eliminated, hired)
2. **Given** an admin selects a candidate, **When** they view the candidate detail page, **Then** they see uploaded resume and cover letter, all video recordings with playback controls, downloadable transcripts, and complete menu feedback
3. **Given** an admin is reviewing a candidate's menu feedback, **When** they view a specific dish, **Then** they see the candidate's rating, comments, elimination vote (if any), and any proposed dish photos

---

### User Story 5 - Admin Gallery and Table View Toggle (Priority: P2)

Admins can switch between a gallery-style visual menu feedback view and a table-style aggregated view to compare candidate feedback across dishes and candidates.

**Why this priority**: Different review tasks require different views. Gallery mode enables visual assessment of dish feedback; table mode enables analytical comparison across candidates.

**Independent Test**: Can be tested by toggling between gallery and table views with preserved filters and displaying aggregated feedback. Delivers value by providing flexible review interfaces.

**Acceptance Scenarios**:

1. **Given** an admin is viewing menu feedback across candidates, **When** they select gallery view, **Then** they see a grid of dish photos with overlay showing candidate names, ratings, and feedback counts
2. **Given** an admin is in gallery view, **When** they toggle to table view, **Then** they see a sortable/filterable table showing dishes with aggregated ratings, comment counts, elimination votes, and proposed dish counts from all candidates
3. **Given** an admin has applied filters (e.g., show only appetizers, ratings below 3 stars), **When** they toggle between gallery and table views, **Then** the filters persist and results remain consistent
4. **Given** an admin clicks on a dish in either view, **When** they view dish details, **Then** they see all candidate feedback aggregated: all comments, average rating, elimination vote count, and all proposed dishes

---

### User Story 6 - Admin Management of Interview Prompts (Priority: P3)

Admins can add, edit, and remove interview prompts that candidates see during the video interview wizard, allowing flexible customization of the interview process.

**Why this priority**: Enables customization of the interview process as hiring needs evolve. Not critical for MVP but important for long-term flexibility.

**Independent Test**: Can be tested by adding/editing/removing prompts and verifying candidates see updated prompts. Delivers value by allowing interview customization without code changes.

**Acceptance Scenarios**:

1. **Given** an admin accesses the prompt management interface, **When** they view existing prompts, **Then** they see all current interview prompts in the order candidates will see them
2. **Given** an admin wants to add a new prompt, **When** they create a prompt with question text and optional time limit, **Then** the prompt is added to the interview sequence and new candidates see it
3. **Given** an admin wants to modify the interview, **When** they remove or reorder prompts, **Then** candidates who have not started the interview see the updated sequence (candidates in progress see the original prompts they started with)

---

### Edge Cases

- What happens when a candidate's video upload fails mid-upload due to network interruption? (System should support resumable uploads with progress recovery)
- How does the system handle a candidate who starts the interview but doesn't complete it within a reasonable timeframe? (Draft submissions retained for 30 days; candidate can resume from last completed step)
- What happens if a candidate uploads an unsupported file format for resume or dish proposals? (Clear validation error with supported formats listed; upload blocked until valid format provided)
- How does the system prevent a candidate from viewing other candidates' submissions? (Role-based access control enforced at API level; candidates can only access their own data)
- What happens when multiple admins are reviewing the same candidate simultaneously? (Read-only access for review; no conflicts since admins don't modify candidate data)
- How does transcript generation handle video recordings with poor audio quality or multiple speakers? (Best-effort transcription with confidence scores; admins can flag low-quality transcripts for manual review)
- What happens if the transcription service is completely unavailable or fails? (Graceful degradation: candidate can proceed and complete submission; video is stored; admin sees "transcription unavailable" status and can review video directly without transcript)
- What happens when an admin removes an interview prompt that some candidates have already answered? (Historical responses preserved; prompt only removed from new candidate interviews)

## Requirements *(mandatory)*

### Functional Requirements

**Authentication & Authorization**

- **FR-001**: System MUST allow candidates to create accounts with email and password
- **FR-002**: System MUST verify candidate email addresses before allowing interview access
- **FR-003**: System MUST enforce password complexity (minimum 8 characters, uppercase, lowercase, number, symbol)
- **FR-004**: System MUST provide separate authentication for admin users with role-based access control
- **FR-005**: System MUST prevent candidates from accessing other candidates' data
- **FR-006**: System MUST log all admin access to candidate personal data

**Candidate Profile & Document Upload**

- **FR-007**: Candidates MUST be able to upload resume and cover letter in PDF, DOC, or DOCX format
- **FR-008**: System MUST validate uploaded documents for file size (max 10 MB per file) and format
- **FR-009**: Candidates MUST be able to view and re-upload their documents before starting the interview
- **FR-010**: System MUST store uploaded documents with encryption at rest

**Video Interview Wizard**

- **FR-011**: System MUST present interview prompts in a sequential wizard flow (one prompt at a time)
- **FR-012**: Candidates MUST be able to record video responses up to 5 minutes per prompt
- **FR-013**: Candidates MUST be able to review their video recording and re-record before proceeding
- **FR-014**: System MUST display progress indicator showing current prompt number and total prompts
- **FR-015**: System MUST support chunked/resumable video upload with progress indication
- **FR-016**: System MUST allow candidates to navigate backward to review prior responses before final submission
- **FR-017**: System MUST provide clear error messages for video recording failures (camera permission denied, unsupported format, storage full)

**Video Transcription**

- **FR-018**: System MUST automatically generate text transcripts from uploaded video recordings
- **FR-019**: Transcripts MUST be labeled with prompt text and candidate name (format: "[Prompt] - [Candidate Name].txt")
- **FR-020**: System MUST make transcripts available for download by admins
- **FR-021**: System MUST process transcription asynchronously (candidates and admins see "processing" state until ready)
- **FR-022**: System MUST retain original video and allow candidate submission to proceed even if transcript generation fails; admin MUST see "transcription unavailable" status and have access to video for manual review

**Menu Review & Feedback**

- **FR-023**: System MUST display restaurant menus organized by category (appetizers, mains, desserts, etc.)
- **FR-024**: System MUST display dish photos, names, and descriptions for each menu item
- **FR-025**: Candidates MUST be able to rate each dish on a 1-5 star scale
- **FR-026**: Candidates MUST be able to add text comments for each dish (minimum 0 characters, maximum 500 characters)
- **FR-027**: Candidates MUST be able to vote to eliminate a dish (boolean: yes/no)
- **FR-028**: Candidates MUST be able to upload photos of proposed alternative dishes (optional, max 5 photos per dish, max 5 MB per photo)
- **FR-029**: System MUST auto-save candidate feedback as they progress through menu review
- **FR-030**: Candidates MUST be able to edit feedback before final submission
- **FR-031**: System MUST validate image uploads for format (JPG, PNG, HEIC) and size
- **FR-032**: System MUST allow candidates to submit menu feedback with partial dish coverage (candidates can skip dishes without providing ratings or comments)

**Admin Candidate Review**

- **FR-033**: Admins MUST be able to view list of all candidates with submission status
- **FR-034**: Admins MUST be able to filter candidates by status (incomplete, pending review, reviewed, eliminated, hired)
- **FR-035**: Admins MUST be able to view individual candidate detail page with all submission materials
- **FR-036**: Candidate detail page MUST display uploaded resume and cover letter with download links
- **FR-037**: Candidate detail page MUST display all video recordings with in-browser playback controls
- **FR-038**: Candidate detail page MUST display downloadable transcripts for each video
- **FR-039**: Candidate detail page MUST display complete menu feedback (ratings, comments, elimination votes, proposed dishes)

**Admin Gallery & Table Views**

- **FR-040**: Admins MUST be able to toggle between gallery view and table view for menu feedback analysis
- **FR-041**: Gallery view MUST display dish photos in a grid layout with overlays showing candidate names, ratings, and feedback summary
- **FR-042**: Table view MUST display sortable/filterable table with columns for dish name, category, average rating, comment count, elimination vote count, and proposed dish count
- **FR-043**: System MUST preserve filters and sort state when toggling between gallery and table views
- **FR-044**: Admins MUST be able to click on a dish in either view to see aggregated feedback from all candidates
- **FR-045**: Dish detail view MUST display all candidate comments, ratings, elimination votes, and proposed dish photos

**Admin Prompt Management**

- **FR-046**: Admins MUST be able to view all current interview prompts in sequential order
- **FR-047**: Admins MUST be able to add new interview prompts with question text and optional time limit
- **FR-048**: Admins MUST be able to edit existing interview prompts
- **FR-049**: Admins MUST be able to remove interview prompts
- **FR-050**: Admins MUST be able to reorder interview prompts via drag-and-drop or up/down controls
- **FR-051**: System MUST ensure candidates who have started interviews see the original prompts (no mid-interview changes)
- **FR-052**: System MUST apply prompt changes only to new candidate interviews

**Data Integrity & Audit**

- **FR-053**: System MUST timestamp all candidate submissions (documents, videos, feedback)
- **FR-054**: System MUST prevent candidates from deleting or editing submissions after final submission
- **FR-055**: System MUST log all admin actions (view candidate, download transcript, update candidate status)
- **FR-056**: System MUST retain candidate data for 90 days post-hiring decision (configurable)

### Key Entities *(include if feature involves data)*

- **Candidate**: Represents a chef applicant; attributes include name, email, password (hashed), account status (unverified, active, rejected), submission status (incomplete, submitted, reviewed, eliminated, hired), created timestamp
- **Document**: Represents uploaded resume or cover letter; attributes include candidate ID (foreign key), document type (resume, cover letter), file URL, file size, upload timestamp
- **InterviewPrompt**: Represents a question in the video interview; attributes include prompt text, sequence order, optional time limit, active status, created/modified timestamps
- **VideoRecording**: Represents a candidate's video response; attributes include candidate ID, prompt ID, file URL, duration, upload timestamp, transcription status (pending, processing, completed, failed)
- **Transcript**: Represents transcribed video content; attributes include recording ID (foreign key), text content, confidence score, file URL (for download), generated timestamp
- **Menu**: Represents a restaurant menu; attributes include name, description, active status
- **MenuCategory**: Represents a section of a menu; attributes include menu ID, category name (appetizers, mains, desserts, etc.), sequence order
- **Dish**: Represents a menu item; attributes include menu category ID, dish name, description, photo URLs (array), active status
- **Feedback**: Represents candidate's evaluation of a dish; attributes include candidate ID, dish ID, rating (1-5), comment text, elimination vote (boolean), timestamp
- **ProposedDish**: Represents candidate's alternative dish proposal; attributes include feedback ID (foreign key), candidate ID, dish ID (dish being replaced), photo URLs (array), upload timestamp
- **AdminUser**: Represents staff admin who reviews candidates and manages system; attributes include name, email, password (hashed), created timestamp

## Success Criteria *(mandatory)*

### Measurable Outcomes

**User Experience**

- **SC-001**: Candidates can complete account creation and document upload in under 3 minutes on mobile devices
- **SC-002**: Candidates can complete the entire interview process (profile setup, video interview, menu review) in under 45 minutes on first attempt
- **SC-003**: 90% of candidates successfully upload and submit video recordings on first attempt without technical support
- **SC-004**: Video upload progress indicators provide real-time feedback with less than 2-second update latency
- **SC-005**: 95% of candidates can navigate the wizard flow without accessing help documentation

**Performance**

- **SC-006**: Video uploads (up to 5 minutes, ~100 MB) complete within 3 minutes on average broadband connection
- **SC-007**: Transcript generation completes within 10 minutes for 5-minute video recordings
- **SC-008**: Admin dashboard loads candidate list (100+ candidates) in under 3 seconds
- **SC-009**: Gallery view renders 50+ dish photos with candidate feedback overlays in under 2 seconds on desktop
- **SC-010**: Table view supports sorting and filtering 500+ dishes across 100+ candidates with response time under 1 second

**Data Quality & Integrity**

- **SC-011**: 95% of automatically generated transcripts have sufficient quality for admin review (as measured by confidence scores above 80%)
- **SC-012**: Zero candidate data leakage incidents (candidates viewing other candidates' submissions)
- **SC-013**: 100% of candidate submissions are recoverable after network interruptions (resumable uploads)
- **SC-014**: All admin actions accessing candidate personal data are logged with 100% audit trail completeness

**Business Outcomes**

- **SC-015**: Admins reduce candidate screening time by 40% compared to manual resume review and in-person interviews
- **SC-016**: System supports evaluation of 50+ candidates per hiring cycle without performance degradation
- **SC-017**: Admin time to review single candidate (all materials) reduces to under 15 minutes
- **SC-018**: Hiring team can identify top 10% of candidates based on aggregated menu feedback within 1 hour of final submissions

**Accessibility & Usability**

- **SC-019**: Mobile candidate interface achieves Lighthouse accessibility score above 90
- **SC-020**: Candidate wizard flow has task completion rate above 85% on first attempt (without help)
- **SC-021**: Admin gallery/table toggle feature used by 100% of reviewers (feature adoption indicates value)

### Assumptions

- Candidates have access to devices with camera and microphone (smartphone or laptop)
- Average video response length is 2-3 minutes (max 5 minutes enforced)
- Admins primarily use desktop browsers for review (mobile support secondary)
- Menu content (categories, dishes, photos) is managed by admins outside this feature scope (assumed to be pre-populated or managed via separate admin interface)
- Initial deployment supports English language only (internationalization is future enhancement)
- Transcription service is third-party managed API (AWS Transcribe, Google Speech-to-Text, or AssemblyAI)
- Maximum concurrent candidates during peak hiring: 50-100
- Average candidate submission includes: 2 documents (resume, cover letter), 3-5 video recordings, feedback on 15-25 dishes
- Supported browsers: Chrome, Safari, Firefox, Edge (latest 2 versions)
- Video format: WebM, MP4 (H.264 codec)
- Photo formats: JPG, PNG, HEIC
- Document formats: PDF, DOC, DOCX
