"""
Documents API endpoints
Handles document CRUD, versioning, and generation from workflows
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from app.schemas.document import (
    Document,
    DocumentCreate,
    DocumentUpdate,
    DocumentVersion,
    DocumentWithVersions,
    GenerateDocumentRequest,
    DocumentStatus
)
from app.db.queries import documents as document_queries
from app.services.document_generator import DocumentGenerator

router = APIRouter()


# ==================== DOCUMENT CRUD ====================

@router.post("/", response_model=Document, status_code=status.HTTP_201_CREATED)
def create_document(document: DocumentCreate):
    """Create a new document manually"""
    try:
        db_document = document_queries.create_document(
            project_id=document.project_id,
            workflow_id=document.workflow_id,
            title=document.title,
            content=document.content,
            content_type=document.content_type.value,
            status=document.status.value,
            metadata=document.metadata
        )
        return db_document
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}"
        )


@router.get("/", response_model=List[Document])
def get_documents(
    status_filter: Optional[DocumentStatus] = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all documents with optional filters"""
    try:
        documents = document_queries.get_documents(
            status=status_filter.value if status_filter else None,
            limit=limit,
            offset=offset
        )
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=Document)
def get_document(document_id: int):
    """Get a specific document by ID"""
    document = document_queries.get_document_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    return document


@router.put("/{document_id}", response_model=Document)
def update_document(document_id: int, document_update: DocumentUpdate):
    """Update a document (creates a new version if content changes)"""
    try:
        # Check if document exists
        existing = document_queries.get_document_by_id(document_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        # Update document
        updated = document_queries.update_document(
            document_id=document_id,
            title=document_update.title,
            content=document_update.content,
            content_type=document_update.content_type.value if document_update.content_type else None,
            status=document_update.status.value if document_update.status else None,
            metadata=document_update.metadata,
            create_version=document_update.content is not None,
            change_summary=f"Updated via API"
        )

        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int):
    """Delete a document (cascade deletes versions and chunks)"""
    success = document_queries.delete_document(document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )


# ==================== DOCUMENT GENERATION ====================

@router.post("/generate", response_model=Document, status_code=status.HTTP_201_CREATED)
def generate_document(request: GenerateDocumentRequest):
    """Generate a document from a workflow"""
    try:
        document = DocumentGenerator.generate_document_from_workflow(
            workflow_id=request.workflow_id,
            title=request.title,
            content_type=request.content_type.value,
            auto_validate=request.auto_validate
        )
        return document
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate document: {str(e)}"
        )


# ==================== DOCUMENT STATUS WORKFLOW ====================

@router.post("/{document_id}/validate", response_model=Document)
def validate_document(document_id: int):
    """Change document status to 'validated'"""
    document = document_queries.validate_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    return document


@router.post("/{document_id}/publish", response_model=Document)
def publish_document(document_id: int):
    """Change document status to 'published'"""
    document = document_queries.publish_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    return document


# ==================== DOCUMENT VERSIONS ====================

@router.get("/{document_id}/versions", response_model=List[DocumentVersion])
def get_document_versions(document_id: int):
    """Get all versions of a document"""
    # Check if document exists
    document = document_queries.get_document_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    versions = document_queries.get_document_versions(document_id)
    return versions


@router.get("/{document_id}/versions/{version_number}", response_model=DocumentVersion)
def get_document_version(document_id: int, version_number: int):
    """Get a specific version of a document"""
    version = document_queries.get_version_by_number(document_id, version_number)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_number} of document {document_id} not found"
        )
    return version


@router.get("/{document_id}/with-versions", response_model=DocumentWithVersions)
def get_document_with_versions(document_id: int):
    """Get a document with all its versions"""
    document = document_queries.get_document_with_versions(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    return document


# ==================== PROJECT-SPECIFIC ENDPOINTS ====================

@router.get("/by-project/{project_id}", response_model=List[Document])
def get_documents_by_project(
    project_id: int,
    status_filter: Optional[DocumentStatus] = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all documents for a specific project"""
    try:
        documents = document_queries.get_documents_by_project(
            project_id=project_id,
            status=status_filter.value if status_filter else None,
            limit=limit,
            offset=offset
        )
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.post("/generate-project-summary/{project_id}", response_model=Document, status_code=status.HTTP_201_CREATED)
def generate_project_summary(project_id: int, title: Optional[str] = None):
    """Generate a summary document for all workflows in a project"""
    try:
        document = DocumentGenerator.generate_summary_document_for_project(
            project_id=project_id,
            title=title
        )
        return document
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate project summary: {str(e)}"
        )


@router.get("/stats/by-project/{project_id}")
def get_document_stats(project_id: int):
    """Get document statistics for a project"""
    try:
        stats = document_queries.get_document_stats_by_project(project_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stats: {str(e)}"
        )


# ==================== DOCUMENT INDEXING (HAYSTACK) ====================

@router.post("/{document_id}/index")
def index_document(document_id: int):
    """Index a document using Haystack (for both project and RAG documents)"""
    from app.services.haystack_service import HaystackService

    document = document_queries.get_document_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    try:
        # Index using Haystack
        result = HaystackService.index_document(
            document_id=document_id,
            title=document['title'],
            content=document['content'],
            metadata={
                'project_id': document.get('project_id'),
                'rag_id': document.get('rag_id'),
                'content_type': document['content_type'],
                'status': document['status']
            }
        )

        # Update document metadata
        document_queries.update_document(
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
