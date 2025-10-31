"""Configuration management for MAG MCP Server."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="MAG_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Ollama configuration
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Ollama API host URL",
    )
    embedding_model: str = Field(
        default="nomic-embed-text",
        description="Ollama model for embeddings",
    )
    llm_model: str = Field(
        default="codestral",
        description="Ollama model for code explanations",
    )

    # Codebase configuration
    codebase_root: Path = Field(
        default=Path.cwd(),
        description="Root directory of the C# codebase to index",
    )

    # ChromaDB configuration
    chroma_persist_dir: Path = Field(
        default=Path("./data/chroma"),
        description="Directory for ChromaDB persistent storage",
    )
    chroma_collection_name: str = Field(
        default="csharp_codebase",
        description="Name of the ChromaDB collection",
    )

    # Indexing configuration
    chunk_size_tokens: int = Field(
        default=512,
        description="Target size for code chunks in tokens",
        gt=0,
        le=2048,
    )
    chunk_overlap_tokens: int = Field(
        default=50,
        description="Overlap between chunks for context continuity",
        ge=0,
    )
    max_workers: int = Field(
        default=4,
        description="Number of parallel workers for indexing",
        gt=0,
        le=32,
    )

    # Search configuration
    default_search_results: int = Field(
        default=5,
        description="Default number of search results to return",
        gt=0,
        le=50,
    )
    similarity_threshold: float = Field(
        default=0.7,
        description="Minimum similarity score for search results",
        ge=0.0,
        le=1.0,
    )

    # File filtering
    file_extensions: list[str] = Field(
        default=[".cs"],
        description="File extensions to index",
    )
    exclude_patterns: list[str] = Field(
        default=["**/obj/**", "**/bin/**", "**/packages/**", "**/.vs/**"],
        description="Glob patterns for files/directories to exclude",
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    def model_post_init(self, __context: object) -> None:
        """Ensure directories exist after validation."""
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset the global settings instance (useful for testing)."""
    global _settings
    _settings = None
