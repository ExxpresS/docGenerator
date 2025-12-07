from typing import Optional, List, Dict, Any
from app.db.connection import get_cursor


def create_project(name: str, description: Optional[str] = None) -> Dict[str, Any]:
    """Crée un nouveau projet"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO projects (name, description)
            VALUES (%s, %s)
            RETURNING id, name, description, created_at, updated_at
            """,
            (name, description)
        )
        return dict(cursor.fetchone())


def get_project_by_id(project_id: int) -> Optional[Dict[str, Any]]:
    """Récupère un projet par son ID"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, name, description, created_at, updated_at
            FROM projects
            WHERE id = %s
            """,
            (project_id,)
        )
        result = cursor.fetchone()
        return dict(result) if result else None


def get_all_projects(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """Récupère tous les projets avec pagination"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, name, description, created_at, updated_at
            FROM projects
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, skip)
        )
        return [dict(row) for row in cursor.fetchall()]


def update_project(project_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Met à jour un projet"""
    updates = []
    params = []

    if name is not None:
        updates.append("name = %s")
        params.append(name)
    if description is not None:
        updates.append("description = %s")
        params.append(description)

    if not updates:
        return get_project_by_id(project_id)

    updates.append("updated_at = NOW()")
    params.append(project_id)

    with get_cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE projects
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id, name, description, created_at, updated_at
            """,
            params
        )
        result = cursor.fetchone()
        return dict(result) if result else None


def delete_project(project_id: int) -> bool:
    """Supprime un projet"""
    with get_cursor() as cursor:
        cursor.execute(
            "DELETE FROM projects WHERE id = %s RETURNING id",
            (project_id,)
        )
        return cursor.fetchone() is not None


def count_projects() -> int:
    """Compte le nombre total de projets"""
    with get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM projects")
        return cursor.fetchone()['count']
