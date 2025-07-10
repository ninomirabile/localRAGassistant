"""Local RAG Assistant main application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.api.v1.api import api_router
from src.core.config import settings
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Local RAG Assistant...")
    setup_logging()
    
    # Ensure directories exist
    from src.core.config import ensure_directories
    ensure_directories()
    
    logger.info("Local RAG Assistant started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Local RAG Assistant...")
    
    # STATELESS: pulisco i file temporanei alla chiusura
    try:
        from src.api.dependencies import get_document_service
        document_service = await get_document_service()
        document_service.cleanup_temp_files()
        logger.info("Temporary files cleaned up on shutdown")
    except Exception as e:
        logger.error(f"Failed to cleanup temporary files on shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    description="A powerful local RAG assistant for querying PDF documents",
    lifespan=lifespan,
    docs_url="/docs" if settings.app.debug else None,
    redoc_url=None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Templates
templates = Jinja2Templates(directory="src/templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main application page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Simple health check."""
    return {"status": "healthy", "version": settings.app.version}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.app.debug,
        log_level="debug" if settings.app.debug else "info"
    ) 