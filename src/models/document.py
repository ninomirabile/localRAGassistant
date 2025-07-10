"""Document models."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """Base document model."""

    filename: str = Field(..., description="Document filename")
    title: Optional[str] = Field(None, description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    tags: list[str] = Field(default_factory=list, description="Document tags")


class DocumentCreate(DocumentBase):
    """Document creation model."""

    pass


class DocumentUpdate(BaseModel):
    """Document update model."""

    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None


class Document(DocumentBase):
    """Document model."""

    id: UUID = Field(default_factory=uuid4, description="Document ID")
    file_path: str = Field(..., description="Path to document file")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    pages: Optional[int] = Field(None, description="Number of pages")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    indexed: bool = Field(default=False, description="Whether document is indexed")
    chunk_count: Optional[int] = Field(None, description="Number of chunks")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "filename": "example.pdf",
                    "file_path": "data/example.pdf",
                    "file_size": 1024,
                    "mime_type": "application/pdf",
                }
            ]
        },
    }

    def model_dump(self, **kwargs):
        """Override model_dump to handle UUID and datetime serialization."""
        data = super().model_dump(**kwargs)
        # Convert UUID to string
        if isinstance(data.get("id"), UUID):
            data["id"] = str(data["id"])
        # Convert datetime objects to ISO format strings
        if isinstance(data.get("created_at"), datetime):
            data["created_at"] = data["created_at"].isoformat()
        if isinstance(data.get("updated_at"), datetime):
            data["updated_at"] = data["updated_at"].isoformat()
        return data


class DocumentList(BaseModel):
    """Document list response."""

    documents: list[Document] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    page: int = Field(default=1, description="Current page")
    per_page: int = Field(default=10, description="Documents per page")

    model_config = {"from_attributes": True}

    def model_dump(self, **kwargs):
        """Override model_dump to handle UUID and datetime serialization in documents."""
        data = super().model_dump(**kwargs)
        # Convert UUIDs and datetimes in documents list
        if "documents" in data:
            for doc in data["documents"]:
                if isinstance(doc.get("id"), UUID):
                    doc["id"] = str(doc["id"])
                if isinstance(doc.get("created_at"), datetime):
                    doc["created_at"] = doc["created_at"].isoformat()
                if isinstance(doc.get("updated_at"), datetime):
                    doc["updated_at"] = doc["updated_at"].isoformat()
        return data
