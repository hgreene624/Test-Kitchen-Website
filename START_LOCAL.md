# Quick Start - Local Development

Follow these steps to run the application locally and test Phase 1 setup.

---

## Step 1: Start Infrastructure Services (PostgreSQL + Redis)

Open a terminal and run:

```bash
cd /Users/holdengreene/PycharmProjects/Test-Kitchen-Website
docker-compose up
```

**Wait for services to start** (you'll see "database system is ready to accept connections").

Keep this terminal open (or run with `-d` flag to run in background: `docker-compose up -d`)

---

## Step 2: Set Up Backend

Open a **new terminal** and run:

```bash
cd /Users/holdengreene/PycharmProjects/Test-Kitchen-Website/backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Mac/Linux
# OR
.venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database (creates tables)
# Note: We'll set up Alembic migrations in Phase 2
# For now, the app will create tables on startup

# Start backend server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Test backend:**
- Open browser: http://localhost:8000
- You should see: `{"message": "Welcome to Chef Candidate Evaluation Platform", ...}`
- API Docs: http://localhost:8000/api/docs (Swagger UI)
- Health check: http://localhost:8000/health

Keep this terminal open.

---

## Step 3: Set Up Frontend

Open a **new terminal** (third terminal) and run:

```bash
cd /Users/holdengreene/PycharmProjects/Test-Kitchen-Website/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Expected output:**
```
  ▲ Next.js 15.0.0
  - Local:        http://localhost:3000
  - Ready in 2.3s
```

**Test frontend:**
- Open browser: http://localhost:3000
- You should see the homepage with "Chef Candidate Evaluation Platform"
- Three buttons: "Candidate Sign Up", "Candidate Login", "Admin Login"

---

## What's Working So Far (Phase 1)

✅ **Infrastructure:**
- PostgreSQL database running
- Redis running
- Local file storage directory created

✅ **Backend:**
- FastAPI server running
- Configuration loaded from .env
- Database connection established
- Storage backend initialized (local filesystem)
- Health check endpoint working
- API documentation available

✅ **Frontend:**
- Next.js server running
- Homepage rendering
- Tailwind CSS working
- API client configured (axios with JWT interceptor)

---

## What's NOT Working Yet (Expected)

❌ **No actual pages yet** - Clicking signup/login buttons will show 404 errors
- Pages will be built in Phase 3 (User Story 1)

❌ **No database tables** - Database is empty
- Tables will be created in Phase 2 (models + migrations)

❌ **No API endpoints** - Only health check works
- Endpoints will be built in Phase 3-8 (user stories)

❌ **AssemblyAI integration** - Won't work without API key
- Add your key to `backend/.env` if you have one
- Otherwise it's fine for Phase 1 testing

---

## Troubleshooting

### "Port 5432 already in use" (PostgreSQL)
```bash
# Check if PostgreSQL is already running on your system
lsof -i :5432

# Stop system PostgreSQL (Mac)
brew services stop postgresql

# Or use different port in docker-compose.yml
```

### "Port 6379 already in use" (Redis)
```bash
# Check if Redis is already running
lsof -i :6379

# Stop system Redis (Mac)
brew services stop redis
```

### "Port 8000 already in use" (Backend)
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### "Port 3000 already in use" (Frontend)
```bash
# Frontend will automatically use port 3001 if 3000 is busy
# Or kill the process:
lsof -i :3000
kill -9 <PID>
```

### Backend won't start - "cannot import settings"
```bash
# Make sure you're in the right directory
cd /Users/holdengreene/PycharmProjects/Test-Kitchen-Website/backend

# Make sure virtual environment is activated
source .venv/bin/activate

# Check if .env file exists
ls -la .env
```

### Frontend won't start - "Module not found"
```bash
# Delete node_modules and reinstall
cd /Users/holdengreene/PycharmProjects/Test-Kitchen-Website/frontend
rm -rf node_modules
npm install
```

---

## Stopping Everything

### Stop Backend
- Go to backend terminal
- Press `Ctrl+C`

### Stop Frontend
- Go to frontend terminal
- Press `Ctrl+C`

### Stop Docker Services
```bash
# Stop services
docker-compose down

# Stop services and remove volumes (fresh start)
docker-compose down -v
```

---

## Quick Commands Reference

### Start all services:
```bash
# Terminal 1: Infrastructure
docker-compose up

# Terminal 2: Backend
cd backend && source .venv/bin/activate && uvicorn src.main:app --reload

# Terminal 3: Frontend
cd frontend && npm run dev
```

### View logs:
```bash
# Docker services
docker-compose logs -f

# Backend logs
# (visible in terminal where uvicorn is running)

# Frontend logs
# (visible in terminal where npm run dev is running)
```

### Access URLs:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/health

---

## Next Steps

Once you've verified Phase 1 is working:
1. ✅ Backend server starts and responds
2. ✅ Frontend loads homepage
3. ✅ Can access API documentation

Then we can proceed to:
- **Phase 2**: Build database models (12 entities)
- **Phase 3**: Implement authentication and user signup
- **Phase 4**: Add video recording features
- And so on...

---

**Need help?** Check the terminal output for error messages and refer to the Troubleshooting section above.
