"""
RAG API endpoints using Haystack for document indexing
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from typing import List
from app.schemas.rag import RAG, RAGCreate, RAGUpdate, UploadedFile, RAGStats
from app.db.queries import rags as rag_queries
from app.db.queries import documents as doc_queries
from app.services.haystack_service import HaystackService

router = APIRouter()


# ==================== RAG CRUD ====================

@router.post("/", response_model=RAG, status_code=status.HTTP_201_CREATED)
def create_rag(rag: RAGCreate):
    """Create a new RAG collection"""
    try:
        db_rag = rag_queries.create_rag(
            name=rag.name,
            description=rag.description
        )
        return db_rag
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create RAG: {str(e)}"
        )


@router.get("/", response_model=List[RAG])
def get_rags(skip: int = 0, limit: int = 100):
    """Get all RAG collections"""
    try:
        rags = rag_queries.get_all_rags(skip=skip, limit=limit)
        return rags
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve RAGs: {str(e)}"
        )


@router.get("/{rag_id}", response_model=RAG)
def get_rag(rag_id: int):
    """Get a specific RAG by ID"""
    rag = rag_queries.get_rag_by_id(rag_id)
    if not rag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RAG {rag_id} not found"
        )
    return rag


@router.put("/{rag_id}", response_model=RAG)
def update_rag(rag_id: int, rag_update: RAGUpdate):
    """Update a RAG"""
    existing = rag_queries.get_rag_by_id(rag_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RAG {rag_id} not found"
        )

    try:
        updated = rag_queries.update_rag(
            rag_id=rag_id,
            name=rag_update.name,
            description=rag_update.description
        )
        return updated
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update RAG: {str(e)}"
        )


@router.delete("/{rag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rag(rag_id: int):
    """Delete a RAG (cascade deletes documents and files)"""
    # Also delete from Haystack index
    try:
        documents = doc_queries.get_documents_by_rag(rag_id, limit=1000)
        for doc in documents:
            try:
                HaystackService.delete_document_from_index(doc['id'])
            except:
                pass  # Continue even if deletion fails
    except:
        pass

    success = rag_queries.delete_rag(rag_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RAG {rag_id} not found"
        )


@router.get("/{rag_id}/stats", response_model=RAGStats)
def get_rag_stats(rag_id: int):
    """Get statistics for a RAG"""
    rag = rag_queries.get_rag_by_id(rag_id)
    if not rag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RAG {rag_id} not found"
        )

    stats = rag_queries.get_rag_stats(rag_id)
    return stats


# ==================== FILE UPLOAD ====================

@router.post("/{rag_id}/upload", status_code=status.HTTP_201_CREATED)
async def upload_files(
    rag_id: int,
    files: List[UploadFile] = File(...)
):
    """
    Upload files to a RAG collection
    Accepts: .txt, .md, .json
    Creates a document for each file
    """
    # Verify RAG exists
    rag = rag_queries.get_rag_by_id(rag_id)
    if not rag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RAG {rag_id} not found"
        )

    allowed_extensions = {'.txt', '.md', '.json'}
    results = []

    for file in files:
        # Validate file type
        file_ext = '.' + file.filename.rsplit('.', 1)[-1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_ext} not allowed. Use .txt, .md, or .json"
            )

        try:
            # Read file content
            content_bytes = await file.read()

            # Check file size (limit to 10MB)
            if len(content_bytes) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} exceeds 10MB limit"
                )

            content_text = content_bytes.decode('utf-8')

            # Determine content type
            content_type_map = {
                '.txt': 'text',
                '.md': 'markdown',
                '.json': 'json'
            }
            content_type = content_type_map.get(file_ext, 'text')

            # Store uploaded file
            uploaded_file = rag_queries.create_uploaded_file(
                rag_id=rag_id,
                filename=file.filename,
                file_type=file_ext.lstrip('.'),
                file_size=len(content_bytes),
                file_content=content_bytes,
                mime_type=file.content_type,
                metadata={'original_filename': file.filename}
            )

            # Create document from file
            document = doc_queries.create_document_for_rag(
                rag_id=rag_id,
                title=file.filename,
                content=content_text,
                content_type=content_type,
                status='draft',
                metadata={
                    'uploaded_file_id': uploaded_file['id'],
                    'source': 'file_upload',
                    'original_filename': file.filename
                }
            )

            results.append({
                'filename': file.filename,
                'file_id': uploaded_file['id'],
                'document_id': document['id'],
                'status': 'success'
            })

        except UnicodeDecodeError:
            results.append({
                'filename': file.filename,
                'status': 'error',
                'error': 'File is not valid UTF-8 text'
            })
        except Exception as e:
            results.append({
                'filename': file.filename,
                'status': 'error',
                'error': str(e)
            })

    return {
        'rag_id': rag_id,
        'files_processed': len(results),
        'results': results
    }


@router.get("/{rag_id}/files", response_model=List[UploadedFile])
def get_rag_files(rag_id: int):
    """Get all uploaded files for a RAG"""
    rag = rag_queries.get_rag_by_id(rag_id)
    if not rag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RAG {rag_id} not found"
        )

    files = rag_queries.get_uploaded_files_by_rag(rag_id)
    return files


# ==================== DOCUMENTS IN RAG ====================

@router.get("/{rag_id}/documents")
def get_rag_documents(rag_id: int, limit: int = 100, offset: int = 0):
    """Get all documents in a RAG"""
    rag = rag_queries.get_rag_by_id(rag_id)
    if not rag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RAG {rag_id} not found"
        )

    documents = doc_queries.get_documents_by_rag(rag_id, limit=limit, offset=offset)
    return documents


@router.post("/{rag_id}/documents", status_code=status.HTTP_201_CREATED)
def create_rag_document(rag_id: int, document: dict):
    """Create a new document in a RAG collection"""
    rag = rag_queries.get_rag_by_id(rag_id)
    if not rag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RAG {rag_id} not found"
        )

    try:
        doc = doc_queries.create_document_for_rag(
            rag_id=rag_id,
            title=document.get('title'),
            content=document.get('content'),
            content_type=document.get('content_type', 'html'),
            status=document.get('status', 'draft'),
            metadata=document.get('metadata')
        )
        return doc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}"
        )


# ==================== INDEXING WITH HAYSTACK ====================

@router.post("/{rag_id}/documents/{document_id}/index")
def index_document(rag_id: int, document_id: int):
    """
    Index a document using Haystack: chunk content and generate embeddings
    """
    # Verify document belongs to RAG
    document = doc_queries.get_document_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    if document.get('rag_id') != rag_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document {document_id} does not belong to RAG {rag_id}"
        )

    try:
        # Index using Haystack
        result = HaystackService.index_document(
            document_id=document_id,
            title=document['title'],
            content=document['content'],
            metadata={
                'rag_id': rag_id,
                'content_type': document['content_type'],
                'status': document['status']
            }
        )

        # Update document metadata in database
        doc_queries.update_document(
            document_id=document_id,
            is_indexed=True,
            chunks_count=result['chunks_created']
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index document: {str(e)}"
        )


@router.post("/{rag_id}/index-all")
def index_all_rag_documents(rag_id: int):
    """
    Index all documents in a RAG using Haystack
    """
    rag = rag_queries.get_rag_by_id(rag_id)
    if not rag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RAG {rag_id} not found"
        )

    documents = doc_queries.get_documents_by_rag(rag_id, limit=1000)

    results = []
    for doc in documents:
        try:
            result = HaystackService.index_document(
                document_id=doc['id'],
                title=doc['title'],
                content=doc['content'],
                metadata={
                    'rag_id': rag_id,
                    'content_type': doc['content_type'],
                    'status': doc['status']
                }
            )

            # Update document
            doc_queries.update_document(
                document_id=doc['id'],
                is_indexed=True,
                chunks_count=result['chunks_created']
            )

            results.append({
                'document_id': doc['id'],
                'status': 'success',
                **result
            })
        except Exception as e:
            results.append({
                'document_id': doc['id'],
                'status': 'error',
                'error': str(e)
            })

    return {
        'rag_id': rag_id,
        'total_documents': len(documents),
        'results': results
    }


# ==================== SEARCH ====================

@router.post("/{rag_id}/search")
def search_rag(rag_id: int, query: str, top_k: int = 5):
    """
    Semantic search within a RAG collection using Haystack
    """
    rag = rag_queries.get_rag_by_id(rag_id)
    if not rag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RAG {rag_id} not found"
        )

    try:
        results = HaystackService.search_documents(
            query=query,
            rag_id=rag_id,
            top_k=top_k
        )
        return {
            'query': query,
            'rag_id': rag_id,
            'results': results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
