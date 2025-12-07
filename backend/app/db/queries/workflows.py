from typing import Optional, List, Dict, Any
import json
from app.db.connection import get_cursor


def create_workflow(
    project_id: int,
    name: str,
    raw_data: Dict[str, Any],
    workflow_hash: str,
    description: Optional[str] = None,
    url: Optional[str] = None,
    domain: Optional[str] = None,
    duration_ms: Optional[int] = None,
    states: Optional[List[Dict[str, Any]]] = None,
    actions: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Crée un nouveau workflow avec ses états et actions"""
    with get_cursor() as cursor:
        # Insérer le workflow
        cursor.execute(
            """
            INSERT INTO workflows (project_id, name, description, raw_data, workflow_hash, url, domain, duration_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, project_id, name, description, raw_data, workflow_hash, url, domain, duration_ms, created_at, updated_at
            """,
            (project_id, name, description, json.dumps(raw_data), workflow_hash, url, domain, duration_ms)
        )
        workflow = dict(cursor.fetchone())

        # Insérer les états si présents
        if states:
            for state in states:
                cursor.execute(
                    """
                    INSERT INTO workflow_states (workflow_id, state_type, state_data, sequence_order, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (workflow['id'], state['state_type'], json.dumps(state['state_data']),
                     state['sequence_order'], state['timestamp'])
                )

        # Insérer les actions si présentes
        if actions:
            for action in actions:
                cursor.execute(
                    """
                    INSERT INTO workflow_actions (workflow_id, action_type, action_data, sequence_order, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (workflow['id'], action['action_type'], json.dumps(action['action_data']),
                     action['sequence_order'], action['timestamp'])
                )

        return workflow


def get_workflow_by_id(workflow_id: int, include_details: bool = False) -> Optional[Dict[str, Any]]:
    """Récupère un workflow par son ID"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, project_id, name, description, raw_data, workflow_hash, url, domain, duration_ms, created_at, updated_at
            FROM workflows
            WHERE id = %s
            """,
            (workflow_id,)
        )
        result = cursor.fetchone()
        if not result:
            return None

        workflow = dict(result)

        if include_details:
            # Récupérer les états
            cursor.execute(
                """
                SELECT state_type, state_data, sequence_order, timestamp
                FROM workflow_states
                WHERE workflow_id = %s
                ORDER BY sequence_order
                """,
                (workflow_id,)
            )
            workflow['states'] = [dict(row) for row in cursor.fetchall()]

            # Récupérer les actions
            cursor.execute(
                """
                SELECT action_type, action_data, sequence_order, timestamp
                FROM workflow_actions
                WHERE workflow_id = %s
                ORDER BY sequence_order
                """,
                (workflow_id,)
            )
            workflow['actions'] = [dict(row) for row in cursor.fetchall()]

        return workflow


def get_workflows_by_project(project_id: int, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """Récupère tous les workflows d'un projet"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, project_id, name, description, raw_data, workflow_hash, url, domain, duration_ms, created_at, updated_at
            FROM workflows
            WHERE project_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (project_id, limit, skip)
        )
        return [dict(row) for row in cursor.fetchall()]


def get_workflow_by_hash(project_id: int, workflow_hash: str) -> Optional[Dict[str, Any]]:
    """Vérifie si un workflow existe déjà par son hash"""
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, project_id, name, description, raw_data, workflow_hash, url, domain, duration_ms, created_at, updated_at
            FROM workflows
            WHERE project_id = %s AND workflow_hash = %s
            """,
            (project_id, workflow_hash)
        )
        result = cursor.fetchone()
        return dict(result) if result else None


def update_workflow(workflow_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Met à jour un workflow"""
    updates = []
    params = []

    if name is not None:
        updates.append("name = %s")
        params.append(name)
    if description is not None:
        updates.append("description = %s")
        params.append(description)

    if not updates:
        return get_workflow_by_id(workflow_id)

    updates.append("updated_at = NOW()")
    params.append(workflow_id)

    with get_cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE workflows
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id, project_id, name, description, raw_data, workflow_hash, url, domain, duration_ms, created_at, updated_at
            """,
            params
        )
        result = cursor.fetchone()
        return dict(result) if result else None


def delete_workflow(workflow_id: int) -> bool:
    """Supprime un workflow"""
    with get_cursor() as cursor:
        cursor.execute(
            "DELETE FROM workflows WHERE id = %s RETURNING id",
            (workflow_id,)
        )
        return cursor.fetchone() is not None


def count_workflows_by_project(project_id: int) -> int:
    """Compte le nombre de workflows d'un projet"""
    with get_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) as count FROM workflows WHERE project_id = %s",
            (project_id,)
        )
        return cursor.fetchone()['count']
