"""Document endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from src.api.dependencies import DocumentServiceDep, get_document_service
from src.models.document import Document, DocumentCreate, DocumentList, DocumentUpdate
from src.services.document_service import DocumentService
from src.services.rag_service import rag_service_singleton
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=Document, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    document_service: DocumentService = Depends(get_document_service),
    request: Request = None,
) -> Response:
    """Upload a new document."""
    try:
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Create metadata
        metadata = DocumentCreate(filename=file.filename, title=title, description=description, tags=tag_list)

        # Upload document
        document = await document_service.upload_document(file, metadata)
        logger.info(f"Document uploaded: {document.filename}")

        # Se la richiesta è HTMX, restituisco HTML user-friendly
        if request and request.headers.get("HX-Request") == "true":
            return HTMLResponse(
                f'<div class="text-green-700">Documento <b>{document.filename}</b> caricato con successo!</div>'
            )
        # Altrimenti JSON
        return JSONResponse(document.model_dump())

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document",
        )


@router.post("/reset")
async def reset_documents(
    document_service: DocumentService = Depends(get_document_service),
):
    """Delete all documents from memory and reset the index."""
    # STATELESS: uso il nuovo metodo che pulisce solo la memoria
    deleted_count = document_service.reset_documents()
    return {"status": "ok", "deleted": deleted_count}


@router.get("/", response_model=DocumentList)
async def list_documents(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    document_service: DocumentService = Depends(get_document_service),
    request: Request = None,
) -> Response:
    """List all documents."""
    try:
        doc_list = await document_service.get_documents(skip=skip, limit=limit, search=search)
        # Se la richiesta è HTMX, restituisco HTML user-friendly
        if request and request.headers.get("HX-Request") == "true":
            if not doc_list.documents:
                return HTMLResponse(
                    '<div class="text-center py-8 text-gray-500"><svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48"><path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg><p class="mt-2 text-sm">Nessun documento caricato</p><p class="text-xs">Carica un PDF per iniziare</p></div>'
                )
            html = '<ul class="divide-y divide-gray-200">'
            for doc in doc_list.documents:
                html += f'<li class="py-2 flex items-center justify-between"><span class="font-medium">{doc.filename}</span><span class="text-xs text-gray-500">{doc.file_size//1024} KB</span></li>'
            html += "</ul>"
            return HTMLResponse(html)
        # Altrimenti JSON
        return JSONResponse(doc_list.model_dump())
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents",
        )


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: UUID, document_service: DocumentService = Depends(get_document_service)
) -> Document:
    """Get a specific document."""
    document = await document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.get("/{document_id}/download")
async def download_document(document_id: UUID, document_service: DocumentService = Depends(get_document_service)):
    """Download a document file."""
    document = await document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    file_path = document.file_path
    return FileResponse(path=file_path, filename=document.filename, media_type=document.mime_type)


@router.put("/{document_id}", response_model=Document)
async def update_document(
    document_id: UUID,
    update: DocumentUpdate,
    document_service: DocumentService = Depends(get_document_service),
) -> Document:
    """Update document metadata."""
    document = await document_service.update_document(document_id, update)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    logger.info(f"Document updated: {document.filename}")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: UUID, document_service: DocumentService = Depends(get_document_service)):
    """Delete a document."""
    success = await document_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    logger.info(f"Document deleted: {document_id}")


@router.get("/stats/summary")
async def get_document_stats(
    document_service: DocumentService = Depends(get_document_service),
):
    """Get document statistics."""
    try:
        return await document_service.get_document_stats()
    except Exception as e:
        logger.error(f"Failed to get document stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document statistics",
        )
