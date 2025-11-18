"""Main FastAPI application."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database import engine, Base
from app.utils.logger import logger
from app.api import auth, family, documents
from app.schemas import HealthCheckResponse

# Create database tables (if they don't exist)
try:
    Base.metadata.create_all(bind=engine, checkfirst=True)
except Exception as e:
    logger.warning(f"Could not create tables (may already exist): {e}")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered financial document analysis and portfolio tracking",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    from app.services.qdrant_service import qdrant_service

    # Check database
    try:
        from app.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"

    # Check Qdrant
    try:
        qdrant_service.client.get_collections()
        qdrant_status = "healthy"
    except Exception as e:
        logger.error(f"Qdrant health check failed: {str(e)}")
        qdrant_status = "unhealthy"

    return HealthCheckResponse(
        status="healthy" if db_status == "healthy" and qdrant_status == "healthy" else "degraded",
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION,
        database=db_status,
        qdrant=qdrant_status
    )


# Include routers
app.include_router(auth.router)
app.include_router(family.router)
app.include_router(documents.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} starting...")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[-1]}")  # Don't log credentials
    logger.info(f"Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    logger.info("Application started successfully")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Application shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
