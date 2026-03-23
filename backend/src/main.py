"""FastAPI application initialization with CORS middleware and health check."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config.settings import settings
from .config.database import init_db, close_db
from .config.storage import storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup: Initialize database and storage
    await init_db()
    # Note: Local filesystem storage creates directories on init
    # S3/MinIO storage initialization happens when first used
    yield
    # Shutdown: Close database connections
    await close_db()


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for Chef Candidate Evaluation Platform",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Application health status
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.

    Returns:
        dict: API welcome message and documentation links
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/api/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health",
    }


# Register API routers
from .api.v1 import auth, candidates

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(candidates.router, prefix="/api/v1/candidates", tags=["Candidates"])

# TODO: Register additional routers as they are implemented
# from .api.v1 import admin, media, transcriptions
# app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
# app.include_router(media.router, prefix="/api/v1/media", tags=["Media"])
# app.include_router(transcriptions.router, prefix="/api/v1/transcriptions", tags=["Transcriptions"])
