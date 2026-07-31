"""
Configuration settings for MedBot AI

Загружает настройки из переменных окружения (.env файл)
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_PROJECT_ROOT = _BACKEND_DIR.parent


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "MedBot AI"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Paths
    PROJECT_ROOT: Path = _PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "data"
    RAW_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DIR: Path = DATA_DIR / "processed"
    CHROMADB_DIR: Path = DATA_DIR / "chromadb"

    # ChromaDB
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8001
    CHROMADB_COLLECTION_NAME: str = "medical_documents"

    # Embeddings
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"
    EMBEDDING_DEVICE: str = "cpu"  # cpu или cuda
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_DIMENSION: int = 1024  # для multilingual-e5-large

    # RAG
    RAG_CHUNK_SIZE: int = 800  # Токенов на чанк
    RAG_CHUNK_OVERLAP: int = 100
    RAG_TOP_K: int = 10  # Количество чанков для retrieval
    RAG_RERANK_TOP_K: int = 3  # Финальное количество после reranking
    RAG_SIMILARITY_THRESHOLD: float = 0.7

    # LLM / GigaChat
    GIGACHAT_API_KEY: Optional[str] = None
    GIGACHAT_SCOPE: str = "GIGACHAT_API_PERS"
    GIGACHAT_MODEL: str = "GigaChat"
    GIGACHAT_VERIFY_SSL: bool = False
    LLM_MAX_TOKENS: int = 2048
    LLM_TEMPERATURE: float = 0.3

    # Telegram
    TG_BOT_TOKEN: Optional[str] = None
    API_URL: str = "http://127.0.0.1:8000/api/v1"

    # Document Processing
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: list = ["txt", "pdf", "docx", "html"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        # Корень проекта + backend/.env (backend перекрывает)
        env_file = (str(_PROJECT_ROOT / ".env"), str(_BACKEND_DIR / ".env"))
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
settings = Settings()


# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.RAW_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMADB_DIR.mkdir(parents=True, exist_ok=True)
