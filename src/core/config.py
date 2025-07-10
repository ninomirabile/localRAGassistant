"""Configuration management for Local RAG Assistant."""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Application settings."""

    name: str = Field(default="Local RAG Assistant", env="APP_NAME")
    version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")


class ServerSettings(BaseSettings):
    """Server settings."""

    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")


class RAGSettings(BaseSettings):
    """RAG settings."""

    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="RAG_EMBEDDING_MODEL")
    chunk_size: int = Field(default=256, env="RAG_CHUNK_SIZE")
    chunk_overlap: int = Field(default=32, env="RAG_CHUNK_OVERLAP")
    similarity_threshold: float = Field(default=0.8, env="RAG_SIMILARITY_THRESHOLD")
    top_k: int = Field(default=5, env="TOP_K")


class LLMSettings(BaseSettings):
    """LLM settings."""

    provider: str = Field(default="ollama", env="LLM_PROVIDER")
    model: str = Field(default="llama2:7b", env="LLM_MODEL")
    temperature: float = Field(default=0.1, env="LLM_TEMPERATURE")
    max_tokens: int = Field(default=1000, env="LLM_MAX_TOKENS")


class StorageSettings(BaseSettings):
    """Storage settings."""

    data_dir: str = Field(default="data", env="DATA_DIR")
    index_dir: str = Field(default="index", env="INDEX_DIR")
    cache_dir: str = Field(default="cache", env="CACHE_DIR")
    max_file_size: int = Field(default=52428800, env="MAX_FILE_SIZE")  # 50MB


class SecuritySettings(BaseSettings):
    """Security settings."""

    max_upload_size: int = Field(default=52428800, env="MAX_UPLOAD_SIZE")  # 50MB
    allowed_extensions: List[str] = Field(default=[".pdf"], env="ALLOWED_EXTENSIONS")
    rate_limit: int = Field(default=100, env="RATE_LIMIT")


class RedisSettings(BaseSettings):
    """Redis settings."""

    url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    enabled: bool = Field(default=False, env="REDIS_ENABLED")


class Settings(BaseSettings):
    """Main settings class."""

    app: AppSettings = AppSettings()
    server: ServerSettings = ServerSettings()
    rag: RAGSettings = RAGSettings()
    llm: LLMSettings = LLMSettings()
    storage: StorageSettings = StorageSettings()
    security: SecuritySettings = SecuritySettings()
    redis: RedisSettings = RedisSettings()

    # Campi aggiuntivi per supportare le variabili d'ambiente nel .env
    rag_config_file: Optional[str] = Field(default=None, env="RAG_CONFIG_FILE")
    app_host: Optional[str] = Field(default=None, env="APP_HOST")
    app_port: Optional[int] = Field(default=None, env="APP_PORT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Rimuovo temporaneamente il caricamento del file YAML per evitare errori di validazione
        # extra = "allow"  # Permette campi extra se necessario


# Global settings instance
settings = Settings()


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def ensure_directories():
    """Ensure all required directories exist."""
    root = get_project_root()

    directories = [
        root / settings.storage.data_dir,
        root / settings.storage.index_dir,
        root / settings.storage.cache_dir,
        root / "logs",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
