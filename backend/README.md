# Chef Candidate Evaluation Backend

FastAPI backend for the Chef Candidate Evaluation Platform.

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0 (async)
- **Job Queue**: Redis + ARQ for async transcription
- **Storage**: AWS S3 (or MinIO for local dev)
- **Transcription**: AssemblyAI API
- **Authentication**: JWT with bcrypt password hashing

## Setup

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+
- Redis 7+
- AWS S3 or MinIO (for local development)

### Installation

1. Create and activate virtual environment:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run database migrations:
```bash
alembic upgrade head
```

### Running the Server

Development server with auto-reload:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/api/docs
- Health check: http://localhost:8000/health

### Testing

Run tests:
```bash
pytest
```

With coverage:
```bash
pytest --cov=src --cov-report=html
```

### Code Quality

Format code:
```bash
black src/
```

Lint code:
```bash
ruff check src/
```

Type check:
```bash
mypy src/
```

## Project Structure

```
backend/
├── src/
│   ├── api/          # REST API endpoints
│   ├── models/       # Database models
│   ├── services/     # Business logic
│   ├── lib/          # Shared utilities
│   ├── config/       # Configuration
│   ├── workers/      # Background jobs
│   └── main.py       # FastAPI app
├── tests/            # Test suite
├── alembic/          # Database migrations
└── requirements.txt  # Dependencies
```

## API Documentation

When running in development mode, API documentation is available at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Environment Variables

See `.env.example` for all available configuration options.
