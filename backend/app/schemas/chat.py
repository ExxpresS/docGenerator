"""
Pydantic schemas for chat-related requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """Request model for chat messages"""
    message: str = Field(..., min_length=1, description="User message to send to the LLM")
    rag_id: Optional[int] = Field(None, description="Optional RAG collection ID for context retrieval")
    top_k: Optional[int] = Field(None, description="Number of documents to retrieve (default from config)")


class DocumentUsed(BaseModel):
    """Document used in RAG response"""
    title: str = Field(..., description="Document title")
    score: float = Field(..., description="Relevance score")


class ChatResponse(BaseModel):
    """Response model for chat messages"""
    response: str = Field(..., description="LLM generated response")
    duration_ms: float = Field(..., description="Time taken to generate response in milliseconds")
    timestamp: str = Field(..., description="ISO timestamp of response generation")
    model: str = Field(..., description="Model used for generation")
    rag_used: bool = Field(default=False, description="Whether RAG was used")
    documents_used: Optional[List[DocumentUsed]] = Field(None, description="Documents retrieved for context")
    retrieval_time_ms: Optional[float] = Field(None, description="Time spent retrieving documents")


class ChatErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error message")
    error_type: Optional[str] = Field(None, description="Type of error")
