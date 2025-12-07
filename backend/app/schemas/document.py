from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """Document status workflow"""
    DRAFT = "draft"
    VALIDATED = "validated"
    PUBLISHED = "published"


class ContentType(str, Enum):
    """Document content types"""
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"


# --- Document Models ---

class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    content_type: ContentType = ContentType.MARKDOWN
    status: DocumentStatus = DocumentStatus.DRAFT
    metadata: Optional[Dict[str, Any]] = None


class DocumentCreate(BaseModel):
    project_id: int = Field(..., gt=0)
    workflow_id: Optional[int] = Field(None, gt=0)
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    content_type: ContentType = ContentType.MARKDOWN
    status: DocumentStatus = DocumentStatus.DRAFT
    metadata: Optional[Dict[str, Any]] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    content_type: Optional[ContentType] = None
    status: Optional[DocumentStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class Document(BaseModel):
    id: int
    project_id: Optional[int]
    rag_id: Optional[int]
    workflow_id: Optional[int]
    title: str
    content: str
    content_type: str
    status: str
    is_indexed: bool
    metadata: Optional[Dict[str, Any]]
    version: int
    created_at: datetime
    updated_at: datetime
    validated_at: Optional[datetime]
    last_indexed_at: Optional[datetime]
    chunks_count: int

    class Config:
        from_attributes = True


# --- Document Version Models ---

class DocumentVersionBase(BaseModel):
    content: str = Field(..., min_length=1)
    change_summary: Optional[str] = None


class DocumentVersionCreate(DocumentVersionBase):
    document_id: int = Field(..., gt=0)
    version_number: int = Field(..., gt=0)


class DocumentVersion(BaseModel):
    id: int
    document_id: int
    content: str
    version_number: int
    change_summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Document Generation Request ---

class GenerateDocumentRequest(BaseModel):
    """Request to generate a document from a workflow"""
    workflow_id: int = Field(..., gt=0)
    title: Optional[str] = None
    content_type: ContentType = ContentType.MARKDOWN
    auto_validate: bool = False


# --- Document with Versions ---

class DocumentWithVersions(Document):
    """Document with all its versions"""
    versions: list[DocumentVersion] = []
