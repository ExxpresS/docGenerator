"""
Haystack RAG Service
Manages document indexing and retrieval using Haystack pipelines
"""
from typing import List, Dict, Any, Optional
from haystack import Pipeline, Document
from haystack.utils import Secret
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.writers import DocumentWriter
from haystack_integrations.document_stores.pgvector import PgvectorDocumentStore
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Global document store instance (initialized lazily)
_document_store: Optional[PgvectorDocumentStore] = None
_indexing_pipeline: Optional[Pipeline] = None


def get_document_store() -> PgvectorDocumentStore:
    """
    Get or create the PgvectorDocumentStore instance

    The document store connects to the same PostgreSQL database
    and creates its own table for storing Haystack documents
    """
    global _document_store

    if _document_store is None:
        # Parse DATABASE_URL to get connection parameters
        # Format: postgresql://user:password@host:port/database
        db_url = settings.DATABASE_URL

        # Extract components (simplified parsing)
        # For production, use urllib.parse or similar
        if "://" in db_url:
            db_url = db_url.split("://")[1]

        if "@" in db_url:
            credentials, host_db = db_url.split("@")
            user, password = credentials.split(":")
        else:
            raise ValueError("Invalid DATABASE_URL format")

        if "/" in host_db:
            host_port, database = host_db.split("/")
        else:
            raise ValueError("Invalid DATABASE_URL format")

        if ":" in host_port:
            host, port = host_port.split(":")
        else:
            host = host_port
            port = "5432"

        logger.info(f"Initializing PgvectorDocumentStore: {host}:{port}/{database}")

        _document_store = PgvectorDocumentStore(
            connection_string=Secret.from_token(f"postgresql://{user}:{password}@{host}:{port}/{database}"),
            table_name="haystack_documents",
            embedding_dimension=384,  # all-MiniLM-L6-v2 output dimension
            vector_function="cosine_similarity",
            recreate_table=False,  # Don't drop existing data
            search_strategy="hnsw"  # Use HNSW index for fast search
        )

        logger.info("PgvectorDocumentStore initialized successfully")

    return _document_store


def get_indexing_pipeline() -> Pipeline:
    """
    Get or create the document indexing pipeline

    Pipeline components:
    1. DocumentSplitter - Splits documents into chunks
    2. SentenceTransformersDocumentEmbedder - Generates embeddings
    3. DocumentWriter - Writes to document store
    """
    global _indexing_pipeline

    if _indexing_pipeline is None:
        logger.info("Initializing indexing pipeline")

        # Create pipeline
        pipeline = Pipeline()

        # 1. Document Splitter
        splitter = DocumentSplitter(
            split_by="word",
            split_length=settings.CHUNK_SIZE,
            split_overlap=settings.CHUNK_OVERLAP,
            split_threshold=0
        )

        # 2. Embedder
        embedder = SentenceTransformersDocumentEmbedder(
            model=settings.EMBEDDING_MODEL_NAME,
            progress_bar=False
        )

        # 3. Writer
        writer = DocumentWriter(
            document_store=get_document_store()
        )

        # Connect components
        pipeline.add_component("splitter", splitter)
        pipeline.add_component("embedder", embedder)
        pipeline.add_component("writer", writer)

        pipeline.connect("splitter", "embedder")
        pipeline.connect("embedder", "writer")

        _indexing_pipeline = pipeline
        logger.info("Indexing pipeline initialized successfully")

    return _indexing_pipeline


class HaystackService:
    """Service for indexing and searching documents using Haystack"""

    @staticmethod
    def index_document(
        document_id: int,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Index a document: split, embed, and store in vector DB

        Args:
            document_id: ID of the document in our documents table
            title: Document title
            content: Document content
            metadata: Additional metadata to store with chunks

        Returns:
            Indexing results (chunks created, etc.)
        """
        from datetime import datetime
        start_time = datetime.now()

        # Prepare metadata
        doc_metadata = metadata or {}
        doc_metadata.update({
            'document_id': document_id,
            'title': title,
            'indexed_at': start_time.isoformat()
        })

        # Create Haystack Document
        haystack_doc = Document(
            content=content,
            meta=doc_metadata
        )

        # Run indexing pipeline
        pipeline = get_indexing_pipeline()
        result = pipeline.run({
            "splitter": {"documents": [haystack_doc]}
        })

        # Extract results
        documents_written = result.get("writer", {}).get("documents_written", 0)

        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        logger.info(
            f"Indexed document {document_id}: "
            f"{documents_written} chunks in {duration_ms:.2f}ms"
        )

        return {
            'document_id': document_id,
            'chunks_created': documents_written,
            'indexing_time_ms': duration_ms,
            'indexed_at': end_time.isoformat()
        }

    @staticmethod
    def delete_document_from_index(document_id: int) -> int:
        """
        Delete all chunks of a document from the vector store

        Args:
            document_id: ID of the document to remove

        Returns:
            Number of chunks deleted
        """
        document_store = get_document_store()

        # Delete by metadata filter
        deleted_count = document_store.delete_documents(
            filters={"field": "document_id", "operator": "==", "value": document_id}
        )

        logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
        return deleted_count

    @staticmethod
    def search_documents(
        query: str,
        rag_id: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across indexed documents

        Args:
            query: Search query
            rag_id: Optional RAG ID to filter results
            top_k: Number of results to return

        Returns:
            List of matching document chunks with scores
        """
        from haystack.components.embedders import SentenceTransformersTextEmbedder
        from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever

        # Create query embedder
        text_embedder = SentenceTransformersTextEmbedder(
            model=settings.EMBEDDING_MODEL_NAME
        )

        # Get query embedding
        query_result = text_embedder.run(query)
        query_embedding = query_result["embedding"]

        # Build filters
        filters = None
        if rag_id is not None:
            filters = {"field": "rag_id", "operator": "==", "value": rag_id}

        # Search document store
        document_store = get_document_store()
        results = document_store.embedding_retrieval(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters
        )

        # Format results
        formatted_results = []
        for doc in results:
            formatted_results.append({
                'content': doc.content,
                'score': doc.score,
                'metadata': doc.meta
            })

        return formatted_results

    @staticmethod
    def get_index_stats() -> Dict[str, Any]:
        """
        Get statistics about the indexed documents

        Returns:
            Stats dictionary with document counts, etc.
        """
        document_store = get_document_store()

        total_docs = document_store.count_documents()

        return {
            'total_chunks': total_docs,
            'embedding_dimension': 384,
            'model': settings.EMBEDDING_MODEL_NAME
        }
