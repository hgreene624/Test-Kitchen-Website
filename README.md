# Chef Candidate Evaluation Platform

A password-protected web application for evaluating chef candidates through video interviews, menu reviews, and feedback collection.

## Overview

This platform enables:
- **Candidates**: Create accounts, upload credentials, record video responses, and provide menu feedback
- **Admins**: Review candidate submissions with gallery and table views, manage interview prompts, and track hiring decisions

## Tech Stack

### Backend
- FastAPI (Python 3.11+)
- PostgreSQL 15+ with SQLAlchemy 2.0 (async)
- Redis + ARQ for background jobs
- Local filesystem storage (VPS) or S3-compatible storage (optional)
- AssemblyAI for video transcription

### Frontend
- Next.js 15 (React 18) with TypeScript
- Tailwind CSS + shadcn/ui
- Axios for API communication
- react-media-recorder for video capture

### Deployment
- Hostinger VPS with Ubuntu 22.04+
- Nginx reverse proxy
- Systemd services for process management
- Let's Encrypt SSL certificates

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd Test-Kitchen-Website
```

2. Start infrastructure services:
```bash
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379
- Note: Media storage uses local filesystem (no MinIO needed)

3. Set up backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
alembic upgrade head
uvicorn src.main:app --reload
```

4. Set up frontend (in a new terminal):
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your configuration
npm run dev
```

5. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

## Project Structure

```
.
├── backend/              # FastAPI backend
│   ├── src/
│   │   ├── api/         # REST API endpoints
│   │   ├── models/      # Database models
│   │   ├── services/    # Business logic
│   │   ├── lib/         # Utilities
│   │   └── config/      # Configuration
│   └── tests/           # Backend tests
├── frontend/            # Next.js frontend
│   ├── src/
│   │   ├── app/         # App router pages
│   │   ├── components/  # UI components
│   │   ├── pages/       # Page components
│   │   └── services/    # API services
│   └── tests/           # Frontend tests
├── specs/               # Feature specifications
└── docker-compose.yml   # Development infrastructure
```

## Development Workflow

### Backend Development

```bash
cd backend
source .venv/bin/activate

# Run server
uvicorn src.main:app --reload

# Run tests
pytest

# Format code
black src/

# Type check
mypy src/
```

### Frontend Development

```bash
cd frontend

# Run dev server
npm run dev

# Run tests
npm run test

# Type check
npm run type-check

# Build for production
npm run build
```

## API Documentation

When running in development mode:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Features

### Phase 1: Setup ✅
- Project structure
- Database configuration
- S3 storage setup
- Development environment (Docker Compose)

### Phase 2: Foundational (In Progress)
- Database models for all entities
- Authentication & authorization
- Storage utilities
- Audit logging

### Phase 3: Candidate Account & Profile (P1)
- Account creation and email verification
- Document upload (resume, cover letter)

### Phase 4: Video Interview (P1)
- Video recording with MediaRecorder API
- Automatic transcription via AssemblyAI
- Chunked/resumable uploads

### Phase 5: Menu Review (P1)
- Menu browsing with categories
- Dish feedback (ratings, comments, elimination votes)
- Proposed dish submissions
- Auto-save functionality

### Phase 6: Admin Submissions View (P2)
- Candidate list with filters
- Complete candidate detail view
- Transcript downloads
- Status management

### Phase 7: Gallery & Table Toggle (P2)
- Gallery view for visual feedback comparison
- Table view for analytical comparison
- Aggregated dish feedback

### Phase 8: Prompt Management (P3)
- Add/edit/remove interview prompts
- Reorder prompts
- Dynamic interview customization

## Environment Configuration

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/chef_candidates

# Redis
REDIS_URL=redis://localhost:6379/0

# Storage (Local Filesystem)
STORAGE_TYPE=local
STORAGE_BASE_PATH=/var/www/chef-candidate-media
STORAGE_BASE_URL=http://localhost:8000/media

# AssemblyAI
ASSEMBLYAI_API_KEY=your_key_here

# JWT
JWT_SECRET_KEY=your_secret_here
JWT_ALGORITHM=HS256

# Application
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME="Chef Candidate Evaluation Platform"
```

## Testing

### Backend Tests
```bash
cd backend
pytest --cov=src --cov-report=html
```

### Frontend Tests
```bash
cd frontend
npm run test           # Unit tests
npm run test:e2e       # E2E tests
```

## Deployment

### Production Deployment (Hostinger VPS)

This application is designed for deployment on a Hostinger VPS with Ubuntu 22.04+.

**Complete deployment guide**: See [DEPLOY_VPS.md](DEPLOY_VPS.md)

**Quick deployment steps:**
1. Set up VPS with Ubuntu 22.04+
2. Install dependencies (Python 3.11, Node.js 20, PostgreSQL 15, Redis, Nginx)
3. Upload application files via SFTP
4. Configure environment variables
5. Set up systemd services
6. Configure Nginx reverse proxy
7. Install SSL certificate with Let's Encrypt

**Storage**: Uses local filesystem on VPS (`/var/www/chef-candidate-media/`)

**Alternative storage options**:
- Self-hosted MinIO on VPS (S3-compatible)
- External S3-compatible service (Backblaze B2, Wasabi, DigitalOcean Spaces)

See deployment guide for detailed instructions.

## Documentation

- [Implementation Plan](specs/001-chef-candidate-evaluation/plan.md)
- [Feature Specification](specs/001-chef-candidate-evaluation/spec.md)
- [Data Model](specs/001-chef-candidate-evaluation/data-model.md)
- [API Contracts](specs/001-chef-candidate-evaluation/contracts/)
- [Technology Research](specs/001-chef-candidate-evaluation/research.md)
- [Implementation Tasks](specs/001-chef-candidate-evaluation/tasks.md)

## License

Proprietary - Test Kitchen Team

## Support

For questions or issues, please contact the development team.
