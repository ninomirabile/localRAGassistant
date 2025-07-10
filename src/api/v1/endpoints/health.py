"""Health check endpoints."""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.api.dependencies import (
    DocumentServiceDep,
    get_document_service,
    get_rag_service,
)
from src.core.config import settings
from src.services.document_service import DocumentService
from src.services.rag_service import RAGService
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app.version,
        "name": settings.app.name,
    }


@router.get("/detailed")
async def detailed_health_check(
    rag_service: RAGService = Depends(get_rag_service),
    document_service: DocumentService = Depends(get_document_service),
) -> Dict[str, Any]:
    """Detailed health check with service status."""
    try:
        # Get service statistics
        index_stats = await rag_service.get_index_stats()
        document_stats = await document_service.get_document_stats()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.app.version,
            "name": settings.app.name,
            "services": {
                "rag": {
                    "status": "healthy",
                    "indexed_documents": index_stats.get("total_documents", 0),
                    "total_chunks": index_stats.get("total_chunks", 0),
                },
                "documents": {
                    "status": "healthy",
                    "total_documents": document_stats.get("total_documents", 0),
                    "total_size_mb": document_stats.get("total_size_mb", 0),
                },
            },
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.app.version,
            "name": settings.app.name,
            "error": str(e),
        }


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """Get simplified system status."""
    try:
        # Check RAG service status
        rag_status = "ready"  # Assume ready if no error

        # Get document count
        try:
            from src.api.dependencies import get_document_service

            document_service = await get_document_service()
            documents = await document_service.get_documents(limit=1000)
            doc_count = documents.total
        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            doc_count = 0

        return {
            "rag_status": rag_status,
            "documents_count": doc_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "rag_status": "error",
            "documents_count": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }
