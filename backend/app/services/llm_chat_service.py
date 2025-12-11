"""
LLM Chat Service
Manages chat conversations using Haystack pipelines and Ollama
"""
from typing import Dict, Any, Optional
from haystack import Pipeline
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret

from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Global chat pipeline instance (initialized lazily)
_chat_pipeline: Optional[Pipeline] = None


def get_chat_pipeline() -> Pipeline:
    """
    Get or create the chat pipeline

    Pipeline components:
    1. PromptBuilder - Formats the user message into a prompt
    2. OpenAIGenerator - Calls Ollama via OpenAI-compatible API
    """
    global _chat_pipeline

    if _chat_pipeline is None:
        logger.info("Initializing Ollama chat pipeline")

        # Create pipeline
        pipeline = Pipeline()

        # 1. Prompt Builder
        #preprompt
        preprompt = """Tu es un assistant expert. Utilise toujours les documents ci-dessous pour répondre de manière complète et précise. réponds en francais.
         Si tu ne trouve pas d'information dans les documents pour répondre tu réponds que tu n'as pas de connaissance sur le sujet"""

        # Template with conditional RAG context
        template = """INSTRUCTION : {{ preprompt }}

        {% if documents %}
        CONTEXT DOCUMENTS:
        {{ documents }}
        
        Utilise UNIQUEMENT les documents ci-dessus pour répondre.
        {% else %}
        {% if rag_requested %}
        IMPORTANT: Aucun document pertinent n'a été trouvé dans la base de connaissances.
        Tu DOIS répondre: "Je n'ai pas trouvé d'information sur ce sujet dans la base de connaissances."
        {% endif %}
        {% endif %}
        
        USER QUESTION: {{ user_message }}
        
        A:"""

        prompt_builder = PromptBuilder(template=template)

        # 2. OpenAI Generator configured for Ollama
        # Ollama provides an OpenAI-compatible API endpoint at /v1
        generator = OpenAIGenerator(
            api_key=Secret.from_token("ollama"),  # Ollama doesn't require real API key
            api_base_url=settings.OLLAMA_BASE_URL + "/v1",
            model=settings.OLLAMA_MODEL,
            generation_kwargs={
                "max_tokens": 1000,
                "temperature": 0.7,
            }
        )

        # Add components to pipeline
        pipeline.add_component("prompt_builder", prompt_builder)
        pipeline.add_component("generator", generator)

        # Connect components
        pipeline.connect("prompt_builder.prompt", "generator.prompt")

        _chat_pipeline = pipeline
        logger.info("Chat pipeline initialized successfully")

    return _chat_pipeline


class LLMChatService:
    """Service for handling chat conversations with LLM"""

    @staticmethod
    def generate_response(
        user_message: str,
        rag_id: Optional[int] = None,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM based on user message

        Args:
            user_message: The user's input message
            rag_id: Optional RAG collection ID for context retrieval
            top_k: Number of documents to retrieve (default from config)

        Returns:
            Dictionary containing the response and metadata
        """
        from datetime import datetime
        start_time = datetime.now()

        # Initialize RAG variables
        documents_context = ""
        documents_used = []
        retrieval_time_ms = None
        rag_requested = rag_id is not None

        try:
            # Retrieve documents from RAG if rag_id is provided
            if rag_id is not None:
                retrieval_start = datetime.now()

                # Import here to avoid circular dependency
                from app.services.haystack_service import HaystackService
                from app.db.queries import rags as rag_queries

                # Validate RAG exists
                rag = rag_queries.get_rag_by_id(rag_id)
                if not rag:
                    raise ValueError(f"RAG collection {rag_id} not found")

                # Determine top_k (use provided value or default from settings)
                effective_top_k = top_k if top_k is not None else settings.RAG_TOP_K_DEFAULT

                # Search documents using HaystackService
                logger.info(f"Searching RAG {rag_id} with query: '{user_message[:50]}...' (top_k={effective_top_k})")
                search_results = HaystackService.search_documents(
                    query=user_message,
                    rag_id=rag_id,
                    top_k=effective_top_k
                )

                # Filter by minimum score threshold
                filtered_results = [
                    result for result in search_results
                    if result['score'] >= settings.RAG_MIN_SCORE_THRESHOLD
                ]

                retrieval_end = datetime.now()
                retrieval_time_ms = (retrieval_end - retrieval_start).total_seconds() * 1000

                logger.info(
                    f"Retrieved {len(search_results)} documents, "
                    f"{len(filtered_results)} after filtering (score >= {settings.RAG_MIN_SCORE_THRESHOLD}), "
                    f"in {retrieval_time_ms:.2f}ms"
                )

                # Format documents for prompt
                if filtered_results:
                    formatted_docs = []
                    for idx, result in enumerate(filtered_results, 1):
                        doc_text = f"Document {idx} (score: {result['score']:.2f}):\n"
                        doc_text += result['content']
                        doc_text += f"\nSource: {result['metadata'].get('title', 'Sans titre')}\n"
                        formatted_docs.append(doc_text)

                        # Store metadata for response
                        documents_used.append({
                            'title': result['metadata'].get('title', 'Sans titre'),
                            'score': result['score']
                        })

                    documents_context = "\n\n".join(formatted_docs)
                    logger.info(f"Formatted {len(filtered_results)} documents for context")
                else:
                    logger.warning(f"No documents found with score >= {settings.RAG_MIN_SCORE_THRESHOLD}")

            # Get the chat pipeline
            pipeline = get_chat_pipeline()

            #preprompt
            preprompt = """Tu es un assistant expert. Utilise toujours les documents ci-dessous pour répondre de manière complète et précise. réponds en francais.
             Si tu ne trouve pas d'information dans les documents pour répondre tu réponds que tu n'as pas de connaissance sur le sujet"""

            # Run the pipeline with RAG context
            result = pipeline.run({
                "prompt_builder": {
                    "user_message": user_message,
                    "documents": documents_context,
                    "preprompt": preprompt,
                    "rag_requested": rag_requested
                }
            })

            # Extract the generated response
            replies = result.get("generator", {}).get("replies", [])

            if not replies:
                raise ValueError("No response generated from LLM")

            response_text = replies[0]

            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            logger.info(f"Generated response in {duration_ms:.2f}ms")

            return {
                "response": response_text,
                "duration_ms": duration_ms,
                "timestamp": end_time.isoformat(),
                "model": settings.OLLAMA_MODEL,
                "rag_used": rag_requested,
                "documents_used": documents_used if documents_used else None,
                "retrieval_time_ms": retrieval_time_ms
            }

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
