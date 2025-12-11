from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # API
    PROJECT_NAME: str = "Workflow Manager"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: str = "*"

    # LLM
    DEFAULT_LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "qwen3:4b"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    # LM Studio (OpenAI-compatible API)
    LM_STUDIO_BASE_URL: str = "http://localhost:1235/v1"
    LM_STUDIO_MODEL: str = "qwen:4b"  # Default model name for LM Studio

    # RAG
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RAG_TOP_K_DEFAULT: int = 5
    RAG_MIN_SCORE_THRESHOLD: float = 0.3  # Minimum relevance score for retrieved documents

    # Security
    SECRET_KEY: str = "change-me-in-production"

    @property
    def cors_origins(self) -> List[str]:
        if self.BACKEND_CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(',')]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
