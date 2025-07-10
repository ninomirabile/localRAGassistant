"""Query models."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Query request model."""

    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    top_k: Optional[int] = Field(
        default=5, ge=1, le=20, description="Number of results to return"
    )
    similarity_threshold: Optional[float] = Field(
        default=0.7, ge=0.0, le=1.0, description="Similarity threshold"
    )
    document_ids: Optional[list[UUID]] = Field(
        default=None, description="Filter by document IDs"
    )


class QueryResponse(BaseModel):
    """Query response model."""

    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    sources: list[dict] = Field(default_factory=list, description="Source documents")
    processing_time: float = Field(..., description="Processing time in seconds")
    tokens_used: Optional[int] = Field(None, description="Tokens used for generation")


class SourceDocument(BaseModel):
    """Source document in query response."""

    document_id: UUID = Field(..., description="Document ID")
    document_title: str = Field(..., description="Document title")
    chunk_text: str = Field(..., description="Relevant text chunk")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    page_number: Optional[int] = Field(None, description="Page number")
    chunk_index: int = Field(..., description="Chunk index in document")
