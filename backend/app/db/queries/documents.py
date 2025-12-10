"""
Document and Document Version SQL queries using pure SQL with psycopg2
"""
from typing import Dict, Any, List, Optional
from app.db.connection import get_cursor
import json


# ==================== DOCUMENT CRUD ====================

def create_document(
    project_id: int,
    title: str,
    content: str,
    content_type: str = "markdown",
    workflow_id: Optional[int] = None,
    status: str = "draft",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new document"""
    with get_cursor() as cursor:
        # Insert document
        cursor.execute(
            """
            INSERT INTO documents (
                project_id, workflow_id, title, content,
                content_type, status, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, project_id, rag_id, workflow_id, title, content,
                      content_type, status, is_indexed, metadata, version,
                      created_at, updated_at, validated_at, last_indexed_at, chunks_count
            """,
            (
                project_id, workflow_id, title, content,
                content_type, status, json.dumps(metadata) if metadata else None
            )
        )
        document = dict(cursor.fetchone())

        # Create initial version in same transaction
        cursor.execute(
            """
            INSERT INTO document_versions (
                document_id, content, version_number, change_summary
            )
            VALUES (%s, %s, %s, %s)
            """,
            (document['id'], content, 1, "Initial version")
        )

        return document


def get_document_by_id(document_id: int) -> Optional[Dict[str, Any]]:
    """Get a document by ID"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, project_id, rag_id, workflow_id, title, content,
                   content_type, status, is_indexed, metadata, version,
                   created_at, updated_at, validated_at, last_indexed_at, chunks_count
            FROM documents
            WHERE id = %s
            """,
            (document_id,)
        )
        result = cursor.fetchone()
        return dict(result) if result else None


def get_documents_by_project(
    project_id: int,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get all documents for a project with optional status filter"""
    with get_cursor() as cursor:
        if status:
            cursor.execute(
                """
                SELECT id, project_id, rag_id, workflow_id, title, content,
                       content_type, status, is_indexed, metadata, version,
                       created_at, updated_at, validated_at, last_indexed_at, chunks_count
                FROM documents
                WHERE project_id = %s AND status = %s
                ORDER BY updated_at DESC
                LIMIT %s OFFSET %s
                """,
                (project_id, status, limit, offset)
            )
        else:
            cursor.execute(
                """
                SELECT id, project_id, rag_id, workflow_id, title, content,
                       content_type, status, is_indexed, metadata, version,
                       created_at, updated_at, validated_at, last_indexed_at, chunks_count
                FROM documents
                WHERE project_id = %s
                ORDER BY updated_at DESC
                LIMIT %s OFFSET %s
                """,
                (project_id, limit, offset)
            )
        return [dict(row) for row in cursor.fetchall()]


def get_documents(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get all documents with optional filters"""
    with get_cursor() as cursor:
        if status:
            cursor.execute(
                """
                SELECT id, project_id, rag_id, workflow_id, title, content,
                       content_type, status, is_indexed, metadata, version,
                       created_at, updated_at, validated_at, last_indexed_at, chunks_count
                FROM documents
                WHERE status = %s
                ORDER BY updated_at DESC
                LIMIT %s OFFSET %s
                """,
                (status, limit, offset)
            )
        else:
            cursor.execute(
                """
                SELECT id, project_id, rag_id, workflow_id, title, content,
                       content_type, status, is_indexed, metadata, version,
                       created_at, updated_at, validated_at, last_indexed_at, chunks_count
                FROM documents
                ORDER BY updated_at DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset)
            )
        return [dict(row) for row in cursor.fetchall()]


def update_document(
    document_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    create_version: bool = True,
    change_summary: Optional[str] = None,
    is_indexed: Optional[bool] = None,
    chunks_count: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Update a document and optionally create a new version"""

    # Get current document
    current_doc = get_document_by_id(document_id)
    if not current_doc:
        return None

    # Build update query dynamically
    update_fields = []
    params = []

    if title is not None:
        update_fields.append("title = %s")
        params.append(title)

    if content is not None:
        update_fields.append("content = %s")
        params.append(content)

    if content_type is not None:
        update_fields.append("content_type = %s")
        params.append(content_type)

    if status is not None:
        update_fields.append("status = %s")
        params.append(status)

        # Set validated_at if status changes to validated
        if status == "validated":
            update_fields.append("validated_at = NOW()")

    if metadata is not None:
        update_fields.append("metadata = %s")
        params.append(json.dumps(metadata))

    if is_indexed is not None:
        update_fields.append("is_indexed = %s")
        params.append(is_indexed)
        if is_indexed:
            update_fields.append("last_indexed_at = NOW()")

    if chunks_count is not None:
        update_fields.append("chunks_count = %s")
        params.append(chunks_count)

    # Always update updated_at
    update_fields.append("updated_at = NOW()")

    if not update_fields:
        return current_doc

    # If content changed, increment version and create version record
    if content is not None and create_version:
        new_version = current_doc['version'] + 1
        update_fields.append("version = %s")
        params.append(new_version)

    params.append(document_id)

    with get_cursor() as cursor:
        query = f"""
            UPDATE documents
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id, project_id, rag_id, workflow_id, title, content,
                      content_type, status, is_indexed, metadata, version,
                      created_at, updated_at, validated_at, last_indexed_at, chunks_count
        """
        cursor.execute(query, params)
        updated_doc = dict(cursor.fetchone())

        # Create version if content changed (in same transaction)
        if content is not None and create_version:
            cursor.execute(
                """
                INSERT INTO document_versions (
                    document_id, content, version_number, change_summary
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    document_id,
                    content,
                    updated_doc['version'],
                    change_summary or f"Updated to version {updated_doc['version']}"
                )
            )

    return updated_doc


def delete_document(document_id: int) -> bool:
    """Delete a document (cascade deletes versions and chunks)"""
    with get_cursor() as cursor:
        cursor.execute(
            "DELETE FROM documents WHERE id = %s RETURNING id",
            (document_id,)
        )
        result = cursor.fetchone()
        return result is not None


def validate_document(document_id: int) -> Optional[Dict[str, Any]]:
    """Change document status to validated"""
    return update_document(
        document_id=document_id,
        status="validated",
        create_version=False
    )


def publish_document(document_id: int) -> Optional[Dict[str, Any]]:
    """Change document status to published"""
    return update_document(
        document_id=document_id,
        status="published",
        create_version=False
    )


def get_document_stats_by_project(project_id: int) -> Dict[str, Any]:
    """Get document statistics for a project"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(*) as total_documents,
                COUNT(*) FILTER (WHERE status = 'draft') as draft_count,
                COUNT(*) FILTER (WHERE status = 'validated') as validated_count,
                COUNT(*) FILTER (WHERE status = 'published') as published_count,
                COUNT(*) FILTER (WHERE is_indexed = true) as indexed_count,
                SUM(chunks_count) as total_chunks
            FROM documents
            WHERE project_id = %s
            """,
            (project_id,)
        )
        return dict(cursor.fetchone())


# ==================== DOCUMENT VERSIONS ====================

def create_document_version(
    document_id: int,
    content: str,
    version_number: int,
    change_summary: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new document version"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO document_versions (
                document_id, content, version_number, change_summary
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id, document_id, content, version_number, change_summary, created_at
            """,
            (document_id, content, version_number, change_summary)
        )
        return dict(cursor.fetchone())


def get_document_versions(document_id: int) -> List[Dict[str, Any]]:
    """Get all versions of a document"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, document_id, content, version_number, change_summary, created_at
            FROM document_versions
            WHERE document_id = %s
            ORDER BY version_number DESC
            """,
            (document_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


def get_version_by_number(document_id: int, version_number: int) -> Optional[Dict[str, Any]]:
    """Get a specific version of a document"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, document_id, content, version_number, change_summary, created_at
            FROM document_versions
            WHERE document_id = %s AND version_number = %s
            """,
            (document_id, version_number)
        )
        result = cursor.fetchone()
        return dict(result) if result else None


def get_document_with_versions(document_id: int) -> Optional[Dict[str, Any]]:
    """Get a document with all its versions"""
    document = get_document_by_id(document_id)
    if not document:
        return None

    document['versions'] = get_document_versions(document_id)
    return document


# ==================== RAG-SPECIFIC FUNCTIONS ====================

def create_document_for_rag(
    rag_id: int,
    title: str,
    content: str,
    content_type: str = "markdown",
    status: str = "draft",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a document for a RAG (not a project)"""
    with get_cursor() as cursor:
        # Insert document
        cursor.execute(
            """
            INSERT INTO documents (
                rag_id, title, content,
                content_type, status, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, project_id, rag_id, workflow_id, title, content,
                      content_type, status, is_indexed, metadata, version,
                      created_at, updated_at, validated_at, last_indexed_at, chunks_count
            """,
            (
                rag_id, title, content,
                content_type, status, json.dumps(metadata) if metadata else None
            )
        )
        document = dict(cursor.fetchone())

        # Create initial version in same transaction
        cursor.execute(
            """
            INSERT INTO document_versions (
                document_id, content, version_number, change_summary
            )
            VALUES (%s, %s, %s, %s)
            """,
            (document['id'], content, 1, "Initial version")
        )

        return document


def get_documents_by_rag(
    rag_id: int,
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get all documents for a RAG with optional filters"""
    with get_cursor() as cursor:
        base_query = """
            SELECT id, project_id, rag_id, workflow_id, title, content,
                   content_type, status, is_indexed, metadata, version,
                   created_at, updated_at, validated_at, last_indexed_at, chunks_count
            FROM documents
            WHERE rag_id = %s
        """
        params = [rag_id]

        if status:
            base_query += " AND status = %s"
            params.append(status)

        base_query += " ORDER BY updated_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(base_query, params)
        return [dict(row) for row in cursor.fetchall()]
