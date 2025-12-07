from fastapi import APIRouter, HTTPException, status
from typing import List
from app.schemas.project import Project, ProjectCreate, ProjectUpdate
from app.db.queries import projects as project_queries

router = APIRouter()


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate):
    """Crée un nouveau projet"""
    try:
        db_project = project_queries.create_project(
            name=project.name,
            description=project.description
        )
        return db_project
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating project: {str(e)}"
        )


@router.get("/", response_model=List[Project])
def get_projects(skip: int = 0, limit: int = 100):
    """Récupère tous les projets"""
    try:
        projects = project_queries.get_all_projects(skip=skip, limit=limit)
        return projects
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching projects: {str(e)}"
        )


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: int):
    """Récupère un projet par son ID"""
    project = project_queries.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    return project


@router.put("/{project_id}", response_model=Project)
def update_project(project_id: int, project: ProjectUpdate):
    """Met à jour un projet"""
    db_project = project_queries.get_project_by_id(project_id)
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )

    try:
        updated_project = project_queries.update_project(
            project_id=project_id,
            name=project.name,
            description=project.description
        )
        return updated_project
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating project: {str(e)}"
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int):
    """Supprime un projet"""
    db_project = project_queries.get_project_by_id(project_id)
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )

    try:
        project_queries.delete_project(project_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting project: {str(e)}"
        )


@router.get("/{project_id}/stats")
def get_project_stats(project_id: int):
    """Récupère les statistiques d'un projet"""
    project = project_queries.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )

    from app.db.queries import workflows as workflow_queries
    workflow_count = workflow_queries.count_workflows_by_project(project_id)

    return {
        "project_id": project_id,
        "workflow_count": workflow_count
    }
