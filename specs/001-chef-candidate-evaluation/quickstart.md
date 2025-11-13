# Local Development Quickstart Guide

**Chef Candidate Evaluation Platform**

Get the full stack running in under 30 minutes.

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** ([download](https://www.python.org/downloads/))
- **Node.js 20+** with npm ([download](https://nodejs.org/))
- **PostgreSQL 15+** ([download](https://www.postgresql.org/download/))
- **Redis 7+** ([download](https://redis.io/download/))
- **Git** ([download](https://git-scm.com/downloads))

**Verify installations:**
```bash
python3 --version  # Should be 3.11 or higher
node --version     # Should be 20.x or higher
psql --version     # Should be 15.x or higher
redis-server --version  # Should be 7.x or higher
```

---

## Project Setup

### 1. Clone Repository and Create Feature Branch

```bash
# Clone the repository
git clone <repository-url>
cd Test-Kitchen-Website

# Create and checkout feature branch
git checkout -b 001-chef-candidate-evaluation
```

### 2. Project Structure Overview

```
Test-Kitchen-Website/
├── backend/           # FastAPI backend (Python)
├── frontend/          # Next.js 15 frontend (React)
├── specs/             # Feature specifications
└── README.md
```

---

## Backend Setup

### 1. Create Python Virtual Environment

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Verify activation (you should see (venv) in your prompt)
which python  # Should point to venv/bin/python
```

### 2. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install backend dependencies
pip install -r requirements.txt
```

**Expected `requirements.txt` packages:**
- fastapi
- uvicorn[standard]
- sqlalchemy[asyncpg]
- asyncpg
- alembic
- pydantic[email]
- python-jose[cryptography]
- passlib[bcrypt]
- python-multipart
- arq
- redis
- assemblyai
- boto3
- python-dotenv

### 3. Environment Variables

Create `.env` file in `backend/` directory:

```bash
# Copy template
cp .env.example .env  # If template exists, otherwise create new file
```

**`.env` template (copy-paste ready):**

```bash
# Application
APP_ENV=development
APP_NAME=Chef Candidate Evaluation Platform
DEBUG=True
SECRET_KEY=your-secret-key-change-this-in-production-min-32-chars
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://chef_user:chef_password@localhost:5432/chef_evaluation_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis (for ARQ job queue)
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=10

# JWT Authentication
JWT_SECRET_KEY=your-jwt-secret-key-change-this-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS (Frontend URL)
CORS_ORIGINS=["http://localhost:3000"]

# AWS S3 (use local filesystem for dev)
USE_LOCAL_STORAGE=True
LOCAL_STORAGE_PATH=./storage
S3_BUCKET_NAME=chef-evaluation-dev
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key

# File Upload Limits
MAX_DOCUMENT_SIZE_MB=10
MAX_VIDEO_SIZE_MB=200
MAX_PHOTO_SIZE_MB=5
MAX_VIDEO_DURATION_SECONDS=300

# AssemblyAI Transcription (optional for dev)
ASSEMBLYAI_API_KEY=your-assemblyai-api-key
MOCK_TRANSCRIPTION=True  # Use mock service for local dev

# Email (for email verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@chefeval.local
SMTP_FROM_NAME=Chef Evaluation Platform
```

**Generate secure keys:**
```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Database Setup

#### Create PostgreSQL Database

```bash
# Start PostgreSQL (if not running)
# On macOS with Homebrew:
brew services start postgresql@15
# On Linux:
sudo systemctl start postgresql

# Create database and user
psql postgres

# In psql prompt:
CREATE USER chef_user WITH PASSWORD 'chef_password';
CREATE DATABASE chef_evaluation_db OWNER chef_user;
GRANT ALL PRIVILEGES ON DATABASE chef_evaluation_db TO chef_user;
\q
```

**Verify connection:**
```bash
psql -U chef_user -d chef_evaluation_db -h localhost
# Enter password: chef_password
# Should connect successfully, then \q to quit
```

#### Run Database Migrations

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial database schema"

# Apply migrations
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade -> abc123, Initial database schema
```

**Verify tables created:**
```bash
psql -U chef_user -d chef_evaluation_db -c "\dt"
```

You should see tables: `candidate`, `admin_user`, `document`, `video_recording`, `transcript`, `menu`, `menu_category`, `dish`, `feedback`, `proposed_dish`, `interview_prompt`, `audit_log`

### 5. Redis Setup

```bash
# Start Redis server
# On macOS with Homebrew:
brew services start redis
# On Linux:
sudo systemctl start redis

# Verify Redis is running
redis-cli ping
# Should respond: PONG
```

---

## Frontend Setup

### 1. Install Node Modules

```bash
# Navigate to frontend directory
cd ../frontend  # From backend/ directory

# Install dependencies
npm install
```

**Expected `package.json` dependencies:**
- next (v15)
- react
- react-dom
- tailwindcss
- @radix-ui/* (shadcn/ui components)
- react-hook-form
- zod
- @tanstack/react-query
- axios
- react-media-recorder (for video recording)

### 2. Environment Variables

Create `.env.local` file in `frontend/` directory:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_TIMEOUT=30000

# Feature Flags
NEXT_PUBLIC_ENABLE_MOCK_TRANSCRIPTION=true
NEXT_PUBLIC_MAX_VIDEO_DURATION_SECONDS=300

# AWS S3 (for frontend direct uploads, optional)
NEXT_PUBLIC_S3_BUCKET=chef-evaluation-dev
NEXT_PUBLIC_S3_REGION=us-east-1
```

### 3. Tailwind CSS Configuration

Verify `tailwind.config.js` exists with proper content paths:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

---

## Development Services

### Running All Services

**Option 1: Manual (3 separate terminals)**

**Terminal 1: Backend API**
```bash
cd backend
source venv/bin/activate  # Activate virtual environment
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Terminal 2: ARQ Worker (for transcription jobs)**
```bash
cd backend
source venv/bin/activate
arq app.workers.transcription.WorkerSettings
```

**Expected output:**
```
INFO Starting worker for WorkerSettings
INFO Starting worker with 1 process
INFO Worker started successfully
```

**Terminal 3: Frontend**
```bash
cd frontend
npm run dev
```

**Expected output:**
```
  ▲ Next.js 15.0.0
  - Local:        http://localhost:3000
  - Network:      http://192.168.1.x:3000

 ✓ Ready in 2.5s
```

**Option 2: Using Process Manager (Recommended)**

Create `Procfile.dev` in project root:

```
api: cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
worker: cd backend && source venv/bin/activate && arq app.workers.transcription.WorkerSettings
frontend: cd frontend && npm run dev
```

Run with [Overmind](https://github.com/DarthSim/overmind) or [Foreman](https://github.com/ddollar/foreman):

```bash
# Install Overmind (recommended)
brew install overmind  # macOS
# or install Foreman
gem install foreman

# Run all services
overmind start -f Procfile.dev
# or
foreman start -f Procfile.dev
```

### Access URLs and Ports

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Main application UI |
| **Backend API** | http://localhost:8000 | REST API endpoints |
| **API Docs (Swagger)** | http://localhost:8000/docs | Interactive API documentation |
| **API Docs (ReDoc)** | http://localhost:8000/redoc | Alternative API documentation |
| **PostgreSQL** | localhost:5432 | Database |
| **Redis** | localhost:6379 | Job queue and cache |

**Verify services:**
```bash
# Check API health
curl http://localhost:8000/health
# Expected: {"status":"healthy","database":"connected","redis":"connected"}

# Check frontend
curl http://localhost:3000
# Expected: HTML response
```

---

## Sample Data Seeding

### 1. Create Admin Account

```bash
cd backend
source venv/bin/activate

# Run seed script
python -m app.scripts.seed_admin
```

Or manually via API:

```bash
curl -X POST http://localhost:8000/api/v1/auth/admin/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@chefeval.local",
    "password": "Admin123!@#",
    "full_name": "Test Admin"
  }'
```

**Expected response:**
```json
{
  "id": "uuid-here",
  "email": "admin@chefeval.local",
  "full_name": "Test Admin",
  "created_at": "2025-11-13T10:00:00Z"
}
```

**Save admin credentials:**
- Email: `admin@chefeval.local`
- Password: `Admin123!@#`

### 2. Seed Menu with Dishes

Create seed script `backend/app/scripts/seed_menu.py`:

```python
import asyncio
from app.db.session import AsyncSessionLocal
from app.models import Menu, MenuCategory, Dish

async def seed_menu():
    async with AsyncSessionLocal() as session:
        # Create menu
        menu = Menu(name="Spring 2025 Menu", description="Seasonal spring dishes", is_active=True)
        session.add(menu)
        await session.flush()

        # Create categories with dishes
        categories_data = {
            "Appetizers": [
                {"name": "Grilled Artichoke Hearts", "description": "With lemon aioli", "price": 12.00},
                {"name": "Spring Pea Soup", "description": "Fresh mint and crème fraîche", "price": 9.00},
                {"name": "Burrata Caprese", "description": "Heirloom tomatoes, basil", "price": 14.00},
                {"name": "Crispy Calamari", "description": "Spicy marinara", "price": 13.00},
                {"name": "Charcuterie Board", "description": "Artisan cheeses and cured meats", "price": 18.00},
            ],
            "Entrees": [
                {"name": "Pan-Seared Salmon", "description": "Asparagus, lemon beurre blanc", "price": 28.00},
                {"name": "Herb-Crusted Lamb Chops", "description": "Rosemary jus, roasted potatoes", "price": 34.00},
                {"name": "Wild Mushroom Risotto", "description": "Truffle oil, parmesan", "price": 22.00},
                {"name": "Grilled Ribeye Steak", "description": "12oz, garlic butter", "price": 38.00},
                {"name": "Chicken Piccata", "description": "Lemon-caper sauce, angel hair pasta", "price": 24.00},
                {"name": "Vegetable Wellington", "description": "Puff pastry, seasonal vegetables", "price": 21.00},
            ],
            "Desserts": [
                {"name": "Tiramisu", "description": "Classic Italian, espresso-soaked", "price": 9.00},
                {"name": "Lemon Tart", "description": "Fresh berries, whipped cream", "price": 8.00},
                {"name": "Chocolate Lava Cake", "description": "Vanilla ice cream", "price": 10.00},
                {"name": "Crème Brûlée", "description": "Vanilla bean, caramelized sugar", "price": 9.00},
                {"name": "Seasonal Fruit Sorbet", "description": "Strawberry, mango, or raspberry", "price": 7.00},
            ],
        }

        for idx, (category_name, dishes) in enumerate(categories_data.items(), start=1):
            category = MenuCategory(
                menu_id=menu.id,
                category_name=category_name,
                sequence_order=idx
            )
            session.add(category)
            await session.flush()

            for dish_data in dishes:
                dish = Dish(
                    category_id=category.id,
                    dish_name=dish_data["name"],
                    description=dish_data["description"],
                    price=dish_data["price"],
                    is_active=True
                )
                session.add(dish)

        await session.commit()
        print(f"✓ Seeded menu with {sum(len(d) for d in categories_data.values())} dishes")

if __name__ == "__main__":
    asyncio.run(seed_menu())
```

**Run seed script:**
```bash
python -m app.scripts.seed_menu
```

### 3. Create Sample Interview Prompts

Create seed script `backend/app/scripts/seed_prompts.py`:

```python
import asyncio
from app.db.session import AsyncSessionLocal
from app.models import InterviewPrompt

async def seed_prompts():
    async with AsyncSessionLocal() as session:
        prompts = [
            {
                "prompt_text": "Why do you want to work in our test kitchen?",
                "sequence_order": 1,
                "time_limit_seconds": 180
            },
            {
                "prompt_text": "Describe your most creative dish and the inspiration behind it.",
                "sequence_order": 2,
                "time_limit_seconds": 240
            },
            {
                "prompt_text": "How do you handle criticism of your culinary work?",
                "sequence_order": 3,
                "time_limit_seconds": 180
            },
            {
                "prompt_text": "Walk us through your approach to developing a new menu item.",
                "sequence_order": 4,
                "time_limit_seconds": 300
            },
            {
                "prompt_text": "What food trend are you most excited about and why?",
                "sequence_order": 5,
                "time_limit_seconds": 180
            },
        ]

        for prompt_data in prompts:
            prompt = InterviewPrompt(**prompt_data, is_active=True)
            session.add(prompt)

        await session.commit()
        print(f"✓ Seeded {len(prompts)} interview prompts")

if __name__ == "__main__":
    asyncio.run(seed_prompts())
```

**Run seed script:**
```bash
python -m app.scripts.seed_prompts
```

### 4. Create Test Candidate (Optional)

```bash
curl -X POST http://localhost:8000/api/v1/auth/candidate/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test.chef@example.com",
    "password": "TestChef123!@#",
    "full_name": "Jane Smith"
  }'
```

**Test candidate credentials:**
- Email: `test.chef@example.com`
- Password: `TestChef123!@#`

---

## Running Tests

### Backend Tests (pytest)

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run specific test types
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/contract/       # API contract tests

# Run with coverage
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_auth.py

# Run tests matching pattern
pytest -k "test_candidate"
```

**Expected output:**
```
========================= test session starts ==========================
collected 87 items

tests/unit/test_auth.py ..................                       [ 20%]
tests/unit/test_models.py .........................              [ 48%]
tests/integration/test_api.py ..........................         [ 78%]
tests/contract/test_candidate_flow.py ..................         [100%]

========================= 87 passed in 12.34s ==========================
```

### Frontend Tests (Jest + React Testing Library)

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode (re-runs on file changes)
npm test -- --watch

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- src/components/VideoRecorder.test.tsx
```

### End-to-End Tests (Playwright)

```bash
cd frontend

# Install Playwright browsers (first time only)
npx playwright install

# Run e2e tests
npm run test:e2e

# Run in UI mode
npm run test:e2e -- --ui

# Run specific test file
npm run test:e2e -- tests/e2e/candidate-flow.spec.ts
```

---

## Development Workflow

### Database Migrations (Alembic)

#### Create Migration
```bash
cd backend
source venv/bin/activate

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add user_preferences table"

# Review generated migration file in alembic/versions/
# Edit if needed, then apply:
alembic upgrade head
```

#### Rollback Migration
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Rollback all migrations
alembic downgrade base
```

#### View Migration History
```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show SQL that would be executed (dry run)
alembic upgrade head --sql
```

### API Documentation (FastAPI)

Access interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

**Features:**
- Browse all API endpoints
- View request/response schemas
- Test endpoints directly in browser
- Download OpenAPI spec (JSON/YAML)

**Try it out:**
1. Navigate to http://localhost:8000/docs
2. Expand `POST /api/v1/auth/candidate/register`
3. Click "Try it out"
4. Fill in request body
5. Click "Execute"
6. View response

---

## Local Storage Simulation (S3 Alternative)

For local development, files are stored in the local filesystem instead of AWS S3.

### Configuration

In `backend/.env`:
```bash
USE_LOCAL_STORAGE=True
LOCAL_STORAGE_PATH=./storage
```

### Directory Structure

```
backend/storage/
├── documents/       # Resume and cover letter uploads
├── videos/          # Video recording uploads
├── transcripts/     # Generated transcript files
└── photos/          # Proposed dish photos
```

### Implementation

The storage service automatically detects `USE_LOCAL_STORAGE` and routes file operations to local filesystem:

```python
# app/services/storage.py (example)
class StorageService:
    def __init__(self):
        self.use_local = os.getenv("USE_LOCAL_STORAGE", "False") == "True"
        self.local_path = Path(os.getenv("LOCAL_STORAGE_PATH", "./storage"))

    async def upload_file(self, file, path: str):
        if self.use_local:
            return await self._upload_local(file, path)
        else:
            return await self._upload_s3(file, path)
```

**Files are accessible via:**
- Direct path: `backend/storage/videos/candidate-uuid/video1.webm`
- API endpoint: `GET /api/v1/media/videos/{video_id}`

### Mock Transcription Service

For local development without AssemblyAI API key, use mock transcription:

In `backend/.env`:
```bash
MOCK_TRANSCRIPTION=True
```

Mock service generates placeholder transcripts:
```
[MOCK TRANSCRIPT]
Prompt: Why do you want to work in our test kitchen?
Candidate: Jane Smith
Generated at: 2025-11-13 10:30:00
Confidence Score: 0.85

This is a mock transcript for local development.
Replace with actual AssemblyAI integration in production.
```

---

## Troubleshooting Common Issues

### Issue 1: PostgreSQL Connection Refused

**Error:**
```
sqlalchemy.exc.OperationalError: could not connect to server: Connection refused
```

**Solution:**
```bash
# Check if PostgreSQL is running
pg_isready

# If not running, start it
brew services start postgresql@15  # macOS
sudo systemctl start postgresql     # Linux

# Verify connection string in .env matches database credentials
psql -U chef_user -d chef_evaluation_db -h localhost
```

### Issue 2: Redis Connection Error

**Error:**
```
redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379. Connection refused.
```

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# If not running, start it
brew services start redis  # macOS
sudo systemctl start redis # Linux

# Verify Redis URL in .env
REDIS_URL=redis://localhost:6379/0
```

### Issue 3: Alembic Migration Conflicts

**Error:**
```
alembic.util.exc.CommandError: Multiple head revisions are present
```

**Solution:**
```bash
# View current heads
alembic heads

# Merge heads
alembic merge heads -m "Merge conflicting migrations"

# Apply merged migration
alembic upgrade head
```

### Issue 4: Node Module Installation Fails

**Error:**
```
npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree
```

**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall with legacy peer deps
npm install --legacy-peer-deps
```

### Issue 5: Frontend Cannot Connect to Backend

**Error in browser console:**
```
Network Error: ERR_CONNECTION_REFUSED
```

**Solution:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check CORS settings in `backend/.env`:
   ```bash
   CORS_ORIGINS=["http://localhost:3000"]
   ```
3. Verify frontend `.env.local`:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
4. Restart both services

### Issue 6: Video Upload Fails

**Error:**
```
413 Request Entity Too Large
```

**Solution:**

Increase file size limit in `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Increase max body size (default 2MB)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    max_body_size=200 * 1024 * 1024,  # 200 MB
)
```

And in Uvicorn startup:
```bash
uvicorn app.main:app --reload --limit-max-requests 0 --timeout-keep-alive 300
```

### Issue 7: ARQ Worker Not Processing Jobs

**Symptom:** Transcription status stuck on "pending"

**Solution:**
```bash
# Check worker is running
ps aux | grep arq

# Check Redis connection
redis-cli
> KEYS arq:*
> LLEN arq:queue

# Restart worker with verbose logging
arq app.workers.transcription.WorkerSettings --verbose
```

### Issue 8: Database Permissions Error

**Error:**
```
psycopg.errors.InsufficientPrivilege: permission denied for table candidate
```

**Solution:**
```bash
psql -U postgres -d chef_evaluation_db

# Grant all privileges to user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chef_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO chef_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO chef_user;
\q
```

---

## Quick Reference

### Common Commands

```bash
# Backend
cd backend && source venv/bin/activate  # Activate Python venv
uvicorn app.main:app --reload            # Run API server
arq app.workers.transcription.WorkerSettings  # Run worker
alembic upgrade head                     # Apply migrations
pytest                                   # Run tests

# Frontend
cd frontend
npm run dev                              # Run dev server
npm test                                 # Run tests
npm run build                            # Production build
npm run lint                             # Run linter

# Database
psql -U chef_user -d chef_evaluation_db  # Connect to database
alembic current                          # Show current migration
alembic history                          # Show migration history

# Redis
redis-cli                                # Connect to Redis
redis-cli FLUSHALL                       # Clear all Redis data (dev only)
```

### Environment Variables Cheat Sheet

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `REDIS_URL` | Yes | - | Redis connection string |
| `SECRET_KEY` | Yes | - | App secret key (min 32 chars) |
| `JWT_SECRET_KEY` | Yes | - | JWT signing key (min 32 chars) |
| `USE_LOCAL_STORAGE` | No | False | Use filesystem instead of S3 |
| `MOCK_TRANSCRIPTION` | No | False | Use mock transcription service |
| `CORS_ORIGINS` | Yes | - | Allowed frontend origins |

### Default Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend API | 8000 | http://localhost:8000 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |

---

## Next Steps

After completing this quickstart:

1. **Read the Feature Specification**: Review `spec.md` for full requirements and user stories
2. **Explore the Data Model**: Review `data-model.md` for database schema and relationships
3. **Review API Contracts**: Check `contracts/` directory for endpoint specifications
4. **Start Development**: Follow the implementation plan in `plan.md`

**Recommended Development Order:**
1. Authentication system (candidate + admin)
2. Document upload (resume + cover letter)
3. Video recording wizard
4. Menu review and feedback
5. Admin dashboard (candidate list)
6. Gallery/table view toggle
7. Transcription integration
8. Admin prompt management

---

## Getting Help

- **API Documentation**: http://localhost:8000/docs
- **Specification**: `specs/001-chef-candidate-evaluation/spec.md`
- **Data Model**: `specs/001-chef-candidate-evaluation/data-model.md`
- **Research**: `specs/001-chef-candidate-evaluation/research.md`

**Common Questions:**
- Q: How do I add a new database field?
  - A: Update SQLAlchemy model → Run `alembic revision --autogenerate -m "message"` → Run `alembic upgrade head`

- Q: How do I test API endpoints?
  - A: Use Swagger UI at http://localhost:8000/docs or write pytest tests in `tests/contract/`

- Q: How do I add a new frontend component?
  - A: Create component in `frontend/components/` → Import shadcn/ui primitives → Style with Tailwind CSS

---

**You're all set! Happy coding!**
