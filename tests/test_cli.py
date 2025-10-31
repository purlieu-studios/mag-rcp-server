"""Tests for CLI script."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mag.scripts.index_codebase import main, progress_callback, setup_logging


class TestProgressCallback:
    """Test progress callback function."""

    def test_progress_callback_basic(self, capsys: pytest.CaptureFixture) -> None:
        """Test progress callback output."""
        progress_callback("Indexing file.cs", 5, 10)

        captured = capsys.readouterr()
        assert "[5/10]" in captured.out
        assert "50.0%" in captured.out
        assert "Indexing file.cs" in captured.out

    def test_progress_callback_zero_total(self, capsys: pytest.CaptureFixture) -> None:
        """Test progress callback with zero total."""
        progress_callback("Starting", 0, 0)

        captured = capsys.readouterr()
        assert "[0/0]" in captured.out


class TestSetupLogging:
    """Test logging setup."""

    def test_setup_logging_verbose(self) -> None:
        """Test verbose logging setup."""
        setup_logging(verbose=True)
        # If this doesn't raise, it worked

    def test_setup_logging_normal(self) -> None:
        """Test normal logging setup."""
        setup_logging(verbose=False)
        # If this doesn't raise, it worked


class TestCLIMain:
    """Test CLI main function."""

    def test_main_check_ollama_available(self) -> None:
        """Test --check-ollama when Ollama is available."""
        with patch("sys.argv", ["mag-index", "--check-ollama"]), patch(
            "mag.scripts.index_codebase.OllamaClient"
        ) as mock_ollama_class:
            mock_ollama = MagicMock()
            mock_ollama_class.return_value = mock_ollama
            mock_ollama.is_available.return_value = True

            result = main()

            assert result == 0
            mock_ollama.is_available.assert_called_once()

    def test_main_check_ollama_unavailable(self) -> None:
        """Test --check-ollama when Ollama is unavailable."""
        with patch("sys.argv", ["mag-index", "--check-ollama"]), patch(
            "mag.scripts.index_codebase.OllamaClient"
        ) as mock_ollama_class:
            mock_ollama = MagicMock()
            mock_ollama_class.return_value = mock_ollama
            mock_ollama.is_available.return_value = False

            result = main()

            assert result == 1

    def test_main_stats(self) -> None:
        """Test --stats option."""
        with patch("sys.argv", ["mag-index", "--stats"]), patch(
            "mag.scripts.index_codebase.CodebaseEmbedder"
        ) as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.return_value = mock_embedder
            mock_embedder.get_index_stats.return_value = {
                "total_chunks": 100,
                "code_types": ["class", "method"],
                "collection_name": "test_collection",
            }

            result = main()

            assert result == 0
            mock_embedder.get_index_stats.assert_called_once()

    def test_main_with_codebase_arg(self, tmp_path: Path) -> None:
        """Test --codebase argument."""
        test_codebase = tmp_path / "code"
        test_codebase.mkdir()

        with patch("sys.argv", ["mag-index", "--codebase", str(test_codebase), "--stats"]), patch(
            "mag.scripts.index_codebase.CodebaseEmbedder"
        ) as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.return_value = mock_embedder
            mock_embedder.get_index_stats.return_value = {
                "total_chunks": 0,
                "code_types": [],
                "collection_name": "test",
            }

            result = main()

            assert result == 0

    def test_main_indexing_success(self) -> None:
        """Test successful indexing."""
        with patch("sys.argv", ["mag-index"]), patch(
            "mag.scripts.index_codebase.CodebaseEmbedder"
        ) as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.return_value = mock_embedder
            mock_embedder.ollama_client.is_available.return_value = True
            mock_embedder.index_codebase.return_value = {
                "files_processed": 5,
                "chunks_created": 20,
                "errors": 0,
            }

            result = main()

            assert result == 0
            mock_embedder.index_codebase.assert_called_once()

    def test_main_indexing_with_errors(self) -> None:
        """Test indexing with some errors."""
        with patch("sys.argv", ["mag-index"]), patch(
            "mag.scripts.index_codebase.CodebaseEmbedder"
        ) as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.return_value = mock_embedder
            mock_embedder.ollama_client.is_available.return_value = True
            mock_embedder.index_codebase.return_value = {
                "files_processed": 5,
                "chunks_created": 15,
                "errors": 2,
            }

            result = main()

            assert result == 1  # Should return error code due to errors

    def test_main_ollama_unavailable(self) -> None:
        """Test indexing when Ollama is unavailable."""
        with patch("sys.argv", ["mag-index"]), patch(
            "mag.scripts.index_codebase.CodebaseEmbedder"
        ) as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.return_value = mock_embedder
            mock_embedder.ollama_client.is_available.return_value = False

            result = main()

            assert result == 1
            # Should not call index_codebase
            mock_embedder.index_codebase.assert_not_called()

    def test_main_clear_option(self) -> None:
        """Test --clear option."""
        with patch("sys.argv", ["mag-index", "--clear"]), patch(
            "mag.scripts.index_codebase.CodebaseEmbedder"
        ) as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.return_value = mock_embedder
            mock_embedder.ollama_client.is_available.return_value = True
            mock_embedder.index_codebase.return_value = {
                "files_processed": 0,
                "chunks_created": 0,
                "errors": 0,
            }

            result = main()

            assert result == 0
            mock_embedder.clear_index.assert_called_once()

    def test_main_keyboard_interrupt(self) -> None:
        """Test handling of keyboard interrupt."""
        with patch("sys.argv", ["mag-index"]), patch(
            "mag.scripts.index_codebase.CodebaseEmbedder"
        ) as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.return_value = mock_embedder
            mock_embedder.ollama_client.is_available.return_value = True
            mock_embedder.index_codebase.side_effect = KeyboardInterrupt()

            result = main()

            assert result == 130  # Standard exit code for SIGINT

    def test_main_indexing_exception(self) -> None:
        """Test handling of indexing exceptions."""
        with patch("sys.argv", ["mag-index"]), patch(
            "mag.scripts.index_codebase.CodebaseEmbedder"
        ) as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.return_value = mock_embedder
            mock_embedder.ollama_client.is_available.return_value = True
            mock_embedder.index_codebase.side_effect = Exception("Indexing failed")

            result = main()

            assert result == 1

    def test_main_verbose_logging(self) -> None:
        """Test -v/--verbose flag."""
        with patch("sys.argv", ["mag-index", "-v", "--stats"]), patch(
            "mag.scripts.index_codebase.CodebaseEmbedder"
        ) as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.return_value = mock_embedder
            mock_embedder.get_index_stats.return_value = {
                "total_chunks": 0,
                "code_types": [],
                "collection_name": "test",
            }

            result = main()

            assert result == 0
