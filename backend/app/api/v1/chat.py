"""
Chat API endpoints
Handles LLM chat interactions via Ollama
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse, ChatErrorResponse
from app.services.llm_chat_service import LLMChatService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    responses={
        500: {"model": ChatErrorResponse, "description": "Internal server error"},
        400: {"model": ChatErrorResponse, "description": "Bad request"}
    }
)
def chat_with_llm(request: ChatRequest):
    """
    Send a message to the LLM and receive a response

    This endpoint uses Haystack pipeline with Ollama as the backend.
    If rag_id is provided, retrieves relevant documents from the RAG collection
    and includes them as context for the LLM response.

    Ollama must be running at the configured endpoint (default: http://localhost:11434)

    Args:
        request: ChatRequest containing the user message and optional rag_id

    Returns:
        ChatResponse with the LLM's response and metadata
    """
    try:
        # Validate message is not empty (Pydantic should catch this, but double-check)
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )

        # Generate response using the LLM chat service (with optional RAG)
        result = LLMChatService.generate_response(
            user_message=request.message.strip(),
            rag_id=request.rag_id,
            top_k=request.top_k
        )

        return ChatResponse(**result)

    except ValueError as e:
        # RAG not found or validation errors
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}"
        )


@router.get("/health")
def chat_health_check():
    """
    Check if the chat service is available

    Returns basic information about the chat configuration
    """
    from app.config import settings

    return {
        "status": "ok",
        "ollama_url": settings.OLLAMA_BASE_URL,
        "model": settings.OLLAMA_MODEL,
        "message": "Chat service is running. Ensure Ollama is active at the configured URL."
    }
