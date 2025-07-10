"""RAG (Retrieval-Augmented Generation) service."""

import asyncio
import time
from pathlib import Path
from typing import List, Optional

from llama_index.core import VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.llms import LLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import SimpleVectorStore
from sentence_transformers import SentenceTransformer

from src.core.config import settings
from src.models.document import Document
from src.models.query import QueryRequest, QueryResponse, SourceDocument
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DummyLLM(LLM):
    """Dummy LLM that does nothing to avoid OpenAI loading."""

    @property
    def metadata(self):
        from llama_index.core.base.llms.types import MessageRole
        from llama_index.core.llms.llm import LLMMetadata

        return LLMMetadata(
            context_window=3900,
            num_output=256,
            is_chat_model=False,
            is_function_calling_model=False,
            model_name="dummy-llm",
            system_role=MessageRole.SYSTEM,
        )

    def complete(self, prompt: str, formatted: bool = False, **kwargs):
        from llama_index.core.base.llms.types import CompletionResponse

        return CompletionResponse(text="Dummy response")

    def stream_complete(self, prompt: str, formatted: bool = False, **kwargs):
        from llama_index.core.base.llms.types import CompletionResponse

        yield CompletionResponse(text="Dummy response")

    def chat(self, messages, **kwargs):
        from llama_index.core.base.llms.types import ChatMessage, ChatResponse

        return ChatResponse(message=ChatMessage(content="Dummy response"))

    def stream_chat(self, messages, **kwargs):
        from llama_index.core.base.llms.types import ChatMessage, ChatResponse

        yield ChatResponse(message=ChatMessage(content="Dummy response"))

    async def achat(self, messages, **kwargs):
        from llama_index.core.base.llms.types import ChatMessage, ChatResponse

        return ChatResponse(message=ChatMessage(content="Dummy response"))

    async def acomplete(self, prompt: str, formatted: bool = False, **kwargs):
        from llama_index.core.base.llms.types import CompletionResponse

        return CompletionResponse(text="Dummy response")

    async def astream_chat(self, messages, **kwargs):
        from llama_index.core.base.llms.types import ChatMessage, ChatResponse

        yield ChatResponse(message=ChatMessage(content="Dummy response"))

    async def astream_complete(self, prompt: str, formatted: bool = False, **kwargs):
        from llama_index.core.base.llms.types import CompletionResponse

        yield CompletionResponse(text="Dummy response")


class SentenceTransformerEmbedding(BaseEmbedding):
    """Wrapper for SentenceTransformer to be compatible with llama_index."""

    def __init__(self, model_name: str):
        """Initialize with model name."""
        super().__init__()
        # Use a different approach to avoid Pydantic field validation
        object.__setattr__(self, "_model", SentenceTransformer(model_name))

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for query."""
        return self._model.encode(query).tolist()

    def _get_text_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        return self._model.encode(text).tolist()

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        return self._model.encode(texts).tolist()

    async def _aget_query_embedding(self, query: str) -> List[float]:
        """Get embedding for query (async version)."""
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        """Get embedding for text (async version)."""
        return self._get_text_embedding(text)

    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts (async version)."""
        return self._get_text_embeddings(texts)


class RAGService:
    """RAG service for document processing and querying."""

    def __init__(self):
        """Initialize RAG service."""
        self.index: Optional[VectorStoreIndex] = None
        self.embedding_model: Optional[SentenceTransformerEmbedding] = None
        self._initialized = False

    async def initialize(self):
        """Initialize the RAG service."""
        if self._initialized:
            return
        logger.info("Initializing RAG service...")
        # Initialize embedding model
        self.embedding_model = SentenceTransformerEmbedding(settings.rag.embedding_model)
        # NON caricare nessun indice da disco: stateless
        self.index = None
        self._initialized = True
        logger.info("RAG service initialized successfully")

    async def _save_index(self):
        """Stateless: non salva nulla su disco."""
        return

    async def _load_index(self):
        """Stateless: non carica nulla da disco."""
        return

    async def add_document(self, document: Document) -> bool:
        """Add document to the index."""
        await self.initialize()
        try:
            # Read document
            documents = await self._read_document(document.file_path)
            logger.info(f"[DEBUG] Documenti estratti: {documents}")
            if not documents:
                logger.error(f"No content extracted from {document.file_path}")
                return False
            # Crea il node_parser
            node_parser = SentenceSplitter(
                chunk_size=settings.rag.chunk_size,
                chunk_overlap=settings.rag.chunk_overlap,
            )
            # SEMPRE ricrea l'indice da zero (stateless)
            self.index = VectorStoreIndex.from_documents(
                documents,
                embed_model=self.embedding_model,
                node_parser=node_parser,
                storage_context=StorageContext.from_defaults(vector_store=SimpleVectorStore()),
                llm=DummyLLM(),  # <--- Usa DummyLLM invece di None per evitare OpenAI
            )
            logger.info(f"[DEBUG] Indice ricreato: {self.index}")
            logger.info(f"[DEBUG] Numero documenti nell'indice: {len(self.index.docstore.docs) if self.index else 0}")
            # Save index
            await self._save_index()
            logger.info(f"Document {document.filename} added to index successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to add document {document.filename}: {e}")
            return False

    async def _read_document(self, file_path: str) -> List:
        """Read document content."""
        try:
            # Use SimpleDirectoryReader for PDF files
            loader = SimpleDirectoryReader(input_files=[file_path], filename_as_id=True)

            documents = loader.load_data()
            return documents

        except Exception as e:
            logger.error(f"Failed to read document {file_path}: {e}")
            return []

    async def query(self, request: QueryRequest) -> QueryResponse:
        """Process a query and return response."""
        await self.initialize()
        start_time = time.time()
        try:
            logger.info(
                f"[DEBUG] Query: l'indice contiene {len(self.index.docstore.docs) if self.index else 0} documenti"
            )
            if self.index is None:
                return QueryResponse(
                    query=request.query,
                    answer="No documents have been indexed yet. Please upload some documents first.",
                    confidence=0.0,
                    sources=[],
                    processing_time=time.time() - start_time,
                )

            # STATELESS: uso solo il retriever senza LLM
            retriever = self.index.as_retriever(similarity_top_k=request.top_k)

            # Execute retrieval
            nodes = await asyncio.to_thread(retriever.retrieve, request.query)

            # Extract sources and build response text
            sources = []
            response_text = ""

            if nodes:
                for i, node in enumerate(nodes):
                    source = SourceDocument(
                        document_id=node.node_id,
                        document_title=node.metadata.get("file_name", "Unknown"),
                        chunk_text=node.text,
                        similarity_score=node.score if hasattr(node, "score") else 0.0,
                        page_number=node.metadata.get("page_label"),
                        chunk_index=node.metadata.get("chunk_index", 0),
                    )
                    sources.append(source.dict())

                    # Build response text from source documents
                    if i == 0:
                        response_text = f"Basandomi sui documenti caricati, ecco cosa ho trovato:\n\n"
                    response_text += (
                        f"**Fonte {i+1} (pagina {node.metadata.get('page_label', 'N/A')}):**\n{node.text}\n\n"
                    )

            if not sources:
                response_text = (
                    "Non ho trovato informazioni rilevanti nei documenti caricati per rispondere alla tua domanda."
                )

            # Calculate confidence (simplified)
            confidence = min(1.0, len(sources) / request.top_k) if sources else 0.0
            processing_time = time.time() - start_time
            return QueryResponse(
                query=request.query,
                answer=response_text,
                confidence=confidence,
                sources=sources,
                processing_time=processing_time,
                tokens_used=0,  # No LLM tokens used
            )
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return QueryResponse(
                query=request.query,
                answer=f"An error occurred while processing your query: {str(e)}",
                confidence=0.0,
                sources=[],
                processing_time=time.time() - start_time,
            )

    async def remove_document(self, document_id: str) -> bool:
        """Remove document from index."""
        # Note: This is a simplified implementation
        # In a production system, you'd need to implement proper document removal
        logger.warning("Document removal not fully implemented")
        return True

    async def get_index_stats(self) -> dict:
        """Get index statistics."""
        await self.initialize()

        if self.index is None:
            return {"total_documents": 0, "total_chunks": 0, "index_size_mb": 0}

        try:
            # Get basic stats
            stats = {
                "total_documents": len(self.index.docstore.docs),
                "total_chunks": len(self.index.index_struct.nodes_dict),
                "index_size_mb": 0,  # Would need to calculate actual size
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {"total_documents": 0, "total_chunks": 0, "index_size_mb": 0}

    def reset_index(self):
        """Resetta completamente lo stato in memoria."""
        self.index = None
        self.embedding_model = None
        self._initialized = False
        logger.info("[DEBUG] Stato RAGService azzerato: index, embedding_model, _initialized")


# Singleton da usare per tutte le dipendenze
rag_service_singleton = RAGService()
