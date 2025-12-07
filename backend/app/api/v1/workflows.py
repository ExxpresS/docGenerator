from fastapi import APIRouter, HTTPException, status, Query
from typing import List
from app.schemas.workflow import Workflow, WorkflowCreate, WorkflowUpdate, WorkflowWithDetails
from app.db.queries import workflows as workflow_queries
from app.db.queries import projects as project_queries

router = APIRouter()


@router.post("/", response_model=Workflow, status_code=status.HTTP_201_CREATED)
def create_workflow(workflow: WorkflowCreate):
    """Crée un nouveau workflow"""
    # Vérifier que le projet existe
    project = project_queries.get_project_by_id(workflow.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {workflow.project_id} not found"
        )

    # Vérifier si le workflow existe déjà (par hash)
    existing = workflow_queries.get_workflow_by_hash(
        workflow.project_id,
        workflow.workflow_hash
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workflow with hash {workflow.workflow_hash} already exists"
        )

    try:
        # Convertir les states et actions en dict
        states = [state.model_dump() for state in workflow.states] if workflow.states else []
        actions = [action.model_dump() for action in workflow.actions] if workflow.actions else []

        db_workflow = workflow_queries.create_workflow(
            project_id=workflow.project_id,
            name=workflow.name,
            raw_data=workflow.raw_data,
            workflow_hash=workflow.workflow_hash,
            description=workflow.description,
            url=workflow.url,
            domain=workflow.domain,
            duration_ms=workflow.duration_ms,
            states=states,
            actions=actions
        )
        return db_workflow
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating workflow: {str(e)}"
        )


@router.get("/project/{project_id}", response_model=List[Workflow])
def get_workflows_by_project(project_id: int, skip: int = 0, limit: int = 100):
    """Récupère tous les workflows d'un projet"""
    # Vérifier que le projet existe
    project = project_queries.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )

    try:
        workflows = workflow_queries.get_workflows_by_project(
            project_id=project_id,
            skip=skip,
            limit=limit
        )
        return workflows
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching workflows: {str(e)}"
        )


@router.get("/{workflow_id}", response_model=WorkflowWithDetails)
def get_workflow(
    workflow_id: int,
    include_details: bool = Query(True, description="Include states and actions")
):
    """Récupère un workflow par son ID"""
    workflow = workflow_queries.get_workflow_by_id(workflow_id, include_details=include_details)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    return workflow


@router.put("/{workflow_id}", response_model=Workflow)
def update_workflow(workflow_id: int, workflow: WorkflowUpdate):
    """Met à jour un workflow"""
    db_workflow = workflow_queries.get_workflow_by_id(workflow_id)
    if not db_workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    try:
        updated_workflow = workflow_queries.update_workflow(
            workflow_id=workflow_id,
            name=workflow.name,
            description=workflow.description
        )
        return updated_workflow
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating workflow: {str(e)}"
        )


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(workflow_id: int):
    """Supprime un workflow"""
    db_workflow = workflow_queries.get_workflow_by_id(workflow_id)
    if not db_workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    try:
        workflow_queries.delete_workflow(workflow_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting workflow: {str(e)}"
        )
