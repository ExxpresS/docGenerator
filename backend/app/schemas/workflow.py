from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class WorkflowStateBase(BaseModel):
    state_type: str
    state_data: Dict[str, Any]
    sequence_order: int
    timestamp: datetime


class WorkflowActionBase(BaseModel):
    action_type: str
    action_data: Dict[str, Any]
    sequence_order: int
    timestamp: datetime


class WorkflowBase(BaseModel):
    project_id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    raw_data: Dict[str, Any]
    workflow_hash: str = Field(..., max_length=64)
    url: Optional[str] = Field(None, max_length=500)
    domain: Optional[str] = Field(None, max_length=255)
    duration_ms: Optional[int] = None


class WorkflowCreate(WorkflowBase):
    states: Optional[List[WorkflowStateBase]] = []
    actions: Optional[List[WorkflowActionBase]] = []


class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class Workflow(WorkflowBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowWithDetails(Workflow):
    states: List[WorkflowStateBase] = []
    actions: List[WorkflowActionBase] = []
