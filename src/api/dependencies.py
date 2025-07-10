"""API dependencies."""

from fastapi import Depends

from src.services.document_service import DocumentService
from src.services.rag_service import RAGService, rag_service_singleton

# Singleton per DocumentService

document_service_singleton = DocumentService(rag_service_singleton)

async def get_rag_service() -> RAGService:
    """Get singleton RAG service instance."""
    await rag_service_singleton.initialize()
    return rag_service_singleton

async def get_document_service() -> DocumentService:
    """Get singleton Document service instance."""
    return document_service_singleton


# Type aliases for dependency injection
RAGServiceDep = Depends(get_rag_service)
DocumentServiceDep = Depends(get_document_service) 