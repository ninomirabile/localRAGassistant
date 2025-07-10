"""Query endpoints."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse

from src.api.dependencies import get_rag_service
from src.models.query import QueryRequest, QueryResponse
from src.services.rag_service import RAGService
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=QueryResponse)
async def query_documents(
    query: str = Form(...),
    top_k: int = Form(5),
    similarity_threshold: float = Form(0.7),
    rag_service: RAGService = Depends(get_rag_service),
    request: Request = None,
) -> Response:
    """Query documents using RAG."""
    try:
        logger.info(f"Processing query: {query[:100]}...")
        req = QueryRequest(
            query=query, top_k=top_k, similarity_threshold=similarity_threshold
        )
        response = await rag_service.query(req)
        logger.info(f"Query completed in {response.processing_time:.2f}s")
        # Se la richiesta è HTMX, restituisco solo l'answer
        if request and request.headers.get("HX-Request") == "true":
            return HTMLResponse(response.answer)
        return JSONResponse(response.model_dump())
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query",
        )


@router.get("/stats/index")
async def get_index_stats(rag_service: RAGService = Depends(get_rag_service)):
    """Get RAG index statistics."""
    try:
        return await rag_service.get_index_stats()
    except Exception as e:
        logger.error(f"Failed to get index stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve index statistics",
        )
