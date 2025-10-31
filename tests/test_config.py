"""Tests for configuration management."""

import os
from pathlib import Path

import pytest

from mag.config import Settings, get_settings, reset_settings


class TestSettings:
    """Test Settings model."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        settings = Settings()

        assert settings.ollama_host == "http://localhost:11434"
        assert settings.embedding_model == "nomic-embed-text"
        assert settings.llm_model == "codestral"
        assert settings.chunk_size_tokens == 512
        assert settings.chunk_overlap_tokens == 50
        assert settings.default_search_results == 5
        assert settings.similarity_threshold == 0.7
        assert settings.file_extensions == [".cs"]
        assert settings.log_level == "INFO"

    def test_chroma_directory_creation(self, tmp_path: Path) -> None:
        """Test that ChromaDB directory is created on initialization."""
        chroma_dir = tmp_path / "test_chroma"
        assert not chroma_dir.exists()

        settings = Settings(chroma_persist_dir=chroma_dir)

        assert chroma_dir.exists()
        assert chroma_dir.is_dir()
        assert settings.chroma_persist_dir == chroma_dir

    def test_environment_variable_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables override defaults."""
        monkeypatch.setenv("MAG_OLLAMA_HOST", "http://custom:8080")
        monkeypatch.setenv("MAG_EMBEDDING_MODEL", "custom-embed")
        monkeypatch.setenv("MAG_CHUNK_SIZE_TOKENS", "1024")
        monkeypatch.setenv("MAG_LOG_LEVEL", "DEBUG")

        settings = Settings()

        assert settings.ollama_host == "http://custom:8080"
        assert settings.embedding_model == "custom-embed"
        assert settings.chunk_size_tokens == 1024
        assert settings.log_level == "DEBUG"

    def test_chunk_size_validation(self) -> None:
        """Test chunk size must be within valid range."""
        # Valid value
        settings = Settings(chunk_size_tokens=512)
        assert settings.chunk_size_tokens == 512

        # Too large
        with pytest.raises(ValueError, match="less than or equal to 2048"):
            Settings(chunk_size_tokens=3000)

        # Too small (must be > 0)
        with pytest.raises(ValueError, match="greater than 0"):
            Settings(chunk_size_tokens=0)

    def test_similarity_threshold_validation(self) -> None:
        """Test similarity threshold must be between 0 and 1."""
        # Valid values
        settings = Settings(similarity_threshold=0.0)
        assert settings.similarity_threshold == 0.0

        settings = Settings(similarity_threshold=1.0)
        assert settings.similarity_threshold == 1.0

        # Invalid values
        with pytest.raises(ValueError):
            Settings(similarity_threshold=-0.1)

        with pytest.raises(ValueError):
            Settings(similarity_threshold=1.1)

    def test_codebase_root_path_conversion(self, tmp_path: Path) -> None:
        """Test that codebase_root is properly converted to Path."""
        settings = Settings(codebase_root=str(tmp_path))
        assert isinstance(settings.codebase_root, Path)
        assert settings.codebase_root == tmp_path

    def test_exclude_patterns_default(self) -> None:
        """Test default exclude patterns are set."""
        settings = Settings()
        expected_patterns = ["**/obj/**", "**/bin/**", "**/packages/**", "**/.vs/**"]
        assert settings.exclude_patterns == expected_patterns


class TestSettingsSingleton:
    """Test singleton pattern for settings."""

    def teardown_method(self) -> None:
        """Reset settings after each test."""
        reset_settings()

    def test_get_settings_returns_same_instance(self) -> None:
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_reset_settings_clears_instance(self) -> None:
        """Test that reset_settings clears the singleton."""
        settings1 = get_settings()
        reset_settings()
        settings2 = get_settings()

        assert settings1 is not settings2

    def test_get_settings_with_env_override(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that environment variables affect singleton."""
        monkeypatch.setenv("MAG_OLLAMA_HOST", "http://test:9999")

        settings = get_settings()
        assert settings.ollama_host == "http://test:9999"


class TestSettingsValidation:
    """Test additional validation rules."""

    def test_max_workers_range(self) -> None:
        """Test max_workers must be in valid range."""
        # Valid values
        settings = Settings(max_workers=1)
        assert settings.max_workers == 1

        settings = Settings(max_workers=32)
        assert settings.max_workers == 32

        # Invalid: too small
        with pytest.raises(ValueError, match="greater than 0"):
            Settings(max_workers=0)

        # Invalid: too large
        with pytest.raises(ValueError, match="less than or equal to 32"):
            Settings(max_workers=33)

    def test_file_extensions_list(self) -> None:
        """Test file_extensions accepts list of strings."""
        settings = Settings(file_extensions=[".cs", ".csx"])
        assert settings.file_extensions == [".cs", ".csx"]

    def test_chunk_overlap_validation(self) -> None:
        """Test chunk overlap must be non-negative."""
        # Valid values
        settings = Settings(chunk_overlap_tokens=0)
        assert settings.chunk_overlap_tokens == 0

        settings = Settings(chunk_overlap_tokens=100)
        assert settings.chunk_overlap_tokens == 100

        # Invalid: negative
        with pytest.raises(ValueError, match="greater than or equal to 0"):
            Settings(chunk_overlap_tokens=-1)
