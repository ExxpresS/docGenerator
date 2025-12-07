from typing import Dict, Any, List, Optional
from app.db.connection import get_cursor
import json


# ==================== RAG CRUD ====================

def create_rag(name: str, description: Optional[str] = None) -> Dict[str, Any]:
    """Create a new RAG collection"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO rags (name, description)
            VALUES (%s, %s)
            RETURNING id, name, description, created_at, updated_at
            """,
            (name, description)
        )
        return dict(cursor.fetchone())


def get_rag_by_id(rag_id: int) -> Optional[Dict[str, Any]]:
    """Get a RAG by ID"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, name, description, created_at, updated_at
            FROM rags
            WHERE id = %s
            """,
            (rag_id,)
        )
        result = cursor.fetchone()
        return dict(result) if result else None


def get_all_rags(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """Get all RAGs with pagination"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, name, description, created_at, updated_at
            FROM rags
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, skip)
        )
        return [dict(row) for row in cursor.fetchall()]


def update_rag(
    rag_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Update a RAG"""
    updates = []
    params = []

    if name is not None:
        updates.append("name = %s")
        params.append(name)
    if description is not None:
        updates.append("description = %s")
        params.append(description)

    if not updates:
        return get_rag_by_id(rag_id)

    updates.append("updated_at = NOW()")
    params.append(rag_id)

    with get_cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE rags
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id, name, description, created_at, updated_at
            """,
            params
        )
        result = cursor.fetchone()
        return dict(result) if result else None


def delete_rag(rag_id: int) -> bool:
    """Delete a RAG (cascade deletes documents, files)"""
    with get_cursor() as cursor:
        cursor.execute(
            "DELETE FROM rags WHERE id = %s RETURNING id",
            (rag_id,)
        )
        return cursor.fetchone() is not None


def get_rag_stats(rag_id: int) -> Dict[str, Any]:
    """Get statistics for a RAG"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(DISTINCT d.id) as document_count,
                COUNT(DISTINCT uf.id) as file_count,
                COUNT(DISTINCT d.id) FILTER (WHERE d.is_indexed = true) as indexed_documents
            FROM rags r
            LEFT JOIN documents d ON d.rag_id = r.id
            LEFT JOIN uploaded_files uf ON uf.rag_id = r.id
            WHERE r.id = %s
            GROUP BY r.id
            """,
            (rag_id,)
        )
        result = cursor.fetchone()
        if result:
            return dict(result)
        return {
            'document_count': 0,
            'file_count': 0,
            'indexed_documents': 0
        }


# ==================== UPLOADED FILES ====================

def create_uploaded_file(
    rag_id: int,
    filename: str,
    file_type: str,
    file_size: int,
    file_content: bytes,
    mime_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Store an uploaded file"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO uploaded_files
            (rag_id, filename, file_type, file_size, file_content, mime_type, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, rag_id, filename, file_type, file_size, mime_type, uploaded_at, metadata
            """,
            (
                rag_id,
                filename,
                file_type,
                file_size,
                file_content,
                mime_type,
                json.dumps(metadata) if metadata else None
            )
        )
        return dict(cursor.fetchone())


def get_uploaded_files_by_rag(rag_id: int) -> List[Dict[str, Any]]:
    """Get all uploaded files for a RAG (without binary content)"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, rag_id, filename, file_type, file_size, mime_type, uploaded_at, metadata
            FROM uploaded_files
            WHERE rag_id = %s
            ORDER BY uploaded_at DESC
            """,
            (rag_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


def get_uploaded_file_content(file_id: int) -> Optional[bytes]:
    """Get the binary content of an uploaded file"""
    with get_cursor() as cursor:
        cursor.execute(
            "SELECT file_content FROM uploaded_files WHERE id = %s",
            (file_id,)
        )
        result = cursor.fetchone()
        return result['file_content'] if result else None


def delete_uploaded_file(file_id: int) -> bool:
    """Delete an uploaded file"""
    with get_cursor() as cursor:
        cursor.execute(
            "DELETE FROM uploaded_files WHERE id = %s RETURNING id",
            (file_id,)
        )
        return cursor.fetchone() is not None
