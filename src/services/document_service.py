"""Document management service."""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import UploadFile

from src.core.config import settings
from src.models.document import Document, DocumentCreate, DocumentList, DocumentUpdate
from src.services.rag_service import RAGService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DocumentService:
    """Service for document management."""

    def __init__(self, rag_service: RAGService):
        """Initialize document service."""
        self.rag_service = rag_service
        # STATELESS: non uso più la directory data/ permanente
        # self.data_dir = Path(settings.storage.data_dir)
        # self.data_dir.mkdir(parents=True, exist_ok=True)

        # STATELESS: uso solo memoria temporanea per la sessione corrente
        self._documents: Dict[UUID, Document] = {}
        self._temp_files: Dict[UUID, Path] = {}

    async def upload_document(self, file: UploadFile, metadata: Optional[DocumentCreate] = None) -> Document:
        """Upload and process a document."""
        # Validate file
        if not self._validate_file(file):
            raise ValueError(f"Invalid file: {file.filename}")

        # Generate document ID
        doc_id = uuid4()

        # STATELESS: salvo il file in una directory temporanea
        temp_dir = Path(tempfile.gettempdir()) / "local_rag_temp"
        temp_dir.mkdir(exist_ok=True)

        file_extension = Path(file.filename).suffix.lower()
        temp_file_path = temp_dir / f"{doc_id}{file_extension}"

        try:
            # Save file to temp directory
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Get file info
            file_size = temp_file_path.stat().st_size

            # Create document record
            document = Document(
                id=doc_id,
                filename=file.filename,
                file_path=str(temp_file_path),
                file_size=file_size,
                mime_type=file.content_type or "application/octet-stream",
                title=metadata.title if metadata else None,
                description=metadata.description if metadata else None,
                tags=metadata.tags if metadata else [],
            )

            # Add to RAG index
            success = await self.rag_service.add_document(document)
            if success:
                document.indexed = True
                # Update chunk count (simplified)
                document.chunk_count = 1  # This should be calculated from actual chunks

                # STATELESS: salvo il documento solo in memoria per questa sessione
                self._documents[doc_id] = document
                self._temp_files[doc_id] = temp_file_path

            logger.info(f"Document uploaded successfully: {document.filename}")
            return document

        except Exception as e:
            # Clean up temp file if upload failed
            if temp_file_path.exists():
                temp_file_path.unlink()
            logger.error(f"Failed to upload document {file.filename}: {e}")
            raise

    def _validate_file(self, file: UploadFile) -> bool:
        """Validate uploaded file."""
        # Check file size
        if file.size and file.size > settings.security.max_upload_size:
            return False

        # Check file extension
        if file.filename:
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in settings.security.allowed_extensions:
                return False

        # Check content type
        if file.content_type and not file.content_type.startswith("application/pdf"):
            return False

        return True

    async def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID."""
        # STATELESS: restituisco solo i documenti caricati in questa sessione
        return self._documents.get(document_id)

    async def get_documents(self, skip: int = 0, limit: int = 10, search: Optional[str] = None) -> DocumentList:
        """Get list of documents."""
        # STATELESS: restituisco solo i documenti caricati in questa sessione
        documents = list(self._documents.values())

        # Apply search filter
        if search:
            documents = [
                doc
                for doc in documents
                if search.lower() in doc.filename.lower()
                or (doc.title and search.lower() in doc.title.lower())
                or (doc.description and search.lower() in doc.description.lower())
            ]

        # Apply pagination
        total = len(documents)
        documents = documents[skip : skip + limit]

        return DocumentList(documents=documents, total=total, page=skip // limit + 1, per_page=limit)

    async def update_document(self, document_id: UUID, update: DocumentUpdate) -> Optional[Document]:
        """Update document metadata."""
        # STATELESS: aggiorno solo i documenti in memoria
        document = self._documents.get(document_id)
        if document:
            # Apply updates
            if update.title is not None:
                document.title = update.title
            if update.description is not None:
                document.description = update.description
            if update.tags is not None:
                document.tags = update.tags

            document.updated_at = datetime.utcnow()

        return document

    async def delete_document(self, document_id: UUID) -> bool:
        """Delete document."""
        try:
            document = self._documents.get(document_id)
            if not document:
                return False

            # Remove from RAG index
            await self.rag_service.remove_document(str(document_id))

            # STATELESS: rimuovo dalla memoria e cancello il file temporaneo
            del self._documents[document_id]

            temp_file_path = self._temp_files.get(document_id)
            if temp_file_path and temp_file_path.exists():
                temp_file_path.unlink()
                del self._temp_files[document_id]

            logger.info(f"Document deleted: {document.filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False

    async def get_document_stats(self) -> dict:
        """Get document statistics."""
        try:
            # STATELESS: calcolo le statistiche solo sui documenti in memoria
            total_size = sum(doc.file_size for doc in self._documents.values())

            return {
                "total_documents": len(self._documents),
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "average_size_mb": (total_size / len(self._documents)) / (1024 * 1024) if self._documents else 0,
            }

        except Exception as e:
            logger.error(f"Failed to get document stats: {e}")
            return {
                "total_documents": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "average_size_mb": 0,
            }

    def reset_documents(self) -> int:
        """Reset all documents (stateless cleanup)."""
        deleted_count = len(self._documents)

        # STATELESS: pulisco tutti i documenti dalla memoria
        self._documents.clear()

        # Cancello tutti i file temporanei
        for temp_file_path in self._temp_files.values():
            try:
                if temp_file_path.exists():
                    temp_file_path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete temp file {temp_file_path}: {e}")

        self._temp_files.clear()

        # Reset RAG index
        self.rag_service.reset_index()

        logger.info(f"Reset completed: {deleted_count} documents removed")
        return deleted_count

    def cleanup_temp_files(self):
        """Clean up temporary files (called on shutdown)."""
        for temp_file_path in self._temp_files.values():
            try:
                if temp_file_path.exists():
                    temp_file_path.unlink()
                    logger.debug(f"Cleaned up temp file: {temp_file_path}")
            except Exception as e:
                logger.error(f"Failed to cleanup temp file {temp_file_path}: {e}")

        self._temp_files.clear()
        logger.info("Temporary files cleanup completed")

    def get_documents_count(self) -> int:
        """Get the number of documents currently in memory."""
        return len(self._documents)


# Test comment for CI
