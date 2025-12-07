from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


# ==================== RAG Models ====================

class RAGBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class RAGCreate(RAGBase):
    pass


class RAGUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class RAG(RAGBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Uploaded File Models ====================

class UploadedFileCreate(BaseModel):
    filename: str
    file_type: str  # txt, md, json
    file_size: int
    mime_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class UploadedFile(BaseModel):
    id: int
    rag_id: int
    filename: str
    file_type: str
    file_size: int
    mime_type: Optional[str]
    uploaded_at: datetime
    metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


# ==================== RAG Stats Model ====================

class RAGStats(BaseModel):
    document_count: int = 0
    file_count: int = 0
    total_chunks: int = 0
    indexed_documents: int = 0
