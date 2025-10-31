"""Tests for Ollama client."""

from unittest.mock import MagicMock, patch

import pytest

from mag.config import Settings
from mag.llm.ollama_client import OllamaClient, OllamaError


class TestOllamaClient:
    """Test OllamaClient functionality."""

    @pytest.fixture
    def mock_ollama_client(self) -> MagicMock:
        """Create a mock Ollama client."""
        with patch("mag.llm.ollama_client.ollama.Client") as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_ollama_client: MagicMock) -> OllamaClient:
        """Create OllamaClient instance with mocked backend."""
        return OllamaClient()

    def test_initialization_with_default_host(
        self,
        mock_ollama_client: MagicMock,
    ) -> None:
        """Test client initialization with default host from settings."""
        client = OllamaClient()

        assert client.host == "http://localhost:11434"
        assert client.embedding_model == "nomic-embed-text"
        assert client.llm_model == "codestral"
        mock_ollama_client.assert_called_once_with(host="http://localhost:11434")

    def test_initialization_with_custom_host(
        self,
        mock_ollama_client: MagicMock,
    ) -> None:
        """Test client initialization with custom host."""
        custom_host = "http://custom:9999"
        client = OllamaClient(host=custom_host)

        assert client.host == custom_host
        mock_ollama_client.assert_called_once_with(host=custom_host)

    def test_embed_success(self, client: OllamaClient) -> None:
        """Test successful embedding generation."""
        expected_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        client.client.embeddings = MagicMock(
            return_value={"embedding": expected_embedding}
        )

        result = client.embed("test text")

        assert result == expected_embedding
        client.client.embeddings.assert_called_once_with(
            model="nomic-embed-text",
            prompt="test text",
        )

    def test_embed_failure(self, client: OllamaClient) -> None:
        """Test embedding generation failure handling."""
        client.client.embeddings = MagicMock(side_effect=Exception("Connection error"))

        with pytest.raises(OllamaError, match="Failed to generate embedding"):
            client.embed("test text")

    def test_embed_batch(self, client: OllamaClient) -> None:
        """Test batch embedding generation."""
        embeddings = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9],
        ]
        client.client.embeddings = MagicMock(
            side_effect=[{"embedding": emb} for emb in embeddings]
        )

        texts = ["text1", "text2", "text3"]
        results = client.embed_batch(texts)

        assert results == embeddings
        assert client.client.embeddings.call_count == 3

    def test_generate_basic(self, client: OllamaClient) -> None:
        """Test basic text generation."""
        expected_response = "Generated code explanation"
        client.client.chat = MagicMock(
            return_value={"message": {"content": expected_response}}
        )

        result = client.generate("Explain this code")

        assert result == expected_response
        client.client.chat.assert_called_once()
        call_args = client.client.chat.call_args
        assert call_args.kwargs["model"] == "codestral"
        assert len(call_args.kwargs["messages"]) == 1
        assert call_args.kwargs["messages"][0]["role"] == "user"
        assert call_args.kwargs["messages"][0]["content"] == "Explain this code"

    def test_generate_with_system_message(self, client: OllamaClient) -> None:
        """Test generation with system message."""
        expected_response = "Expert response"
        client.client.chat = MagicMock(
            return_value={"message": {"content": expected_response}}
        )

        result = client.generate(
            "Analyze this",
            system="You are an expert C# developer",
        )

        assert result == expected_response
        call_args = client.client.chat.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are an expert C# developer"
        assert messages[1]["role"] == "user"

    def test_generate_with_custom_parameters(self, client: OllamaClient) -> None:
        """Test generation with custom temperature and max_tokens."""
        client.client.chat = MagicMock(
            return_value={"message": {"content": "response"}}
        )

        client.generate(
            "test prompt",
            temperature=0.8,
            max_tokens=1000,
        )

        call_args = client.client.chat.call_args
        options = call_args.kwargs["options"]
        assert options["temperature"] == 0.8
        assert options["num_predict"] == 1000

    def test_generate_failure(self, client: OllamaClient) -> None:
        """Test generation failure handling."""
        client.client.chat = MagicMock(side_effect=Exception("Model error"))

        with pytest.raises(OllamaError, match="Failed to generate completion"):
            client.generate("test prompt")

    def test_explain_code_basic(self, client: OllamaClient) -> None:
        """Test basic code explanation."""
        expected_explanation = "This code implements a singleton pattern"
        client.client.chat = MagicMock(
            return_value={"message": {"content": expected_explanation}}
        )

        code = "public class Singleton { private static Singleton instance; }"
        result = client.explain_code(code)

        assert result == expected_explanation
        call_args = client.client.chat.call_args
        messages = call_args.kwargs["messages"]

        # Should have system message
        assert messages[0]["role"] == "system"
        assert "expert C# developer" in messages[0]["content"]

        # Should have user prompt with code
        assert messages[1]["role"] == "user"
        assert code in messages[1]["content"]
        assert "```csharp" in messages[1]["content"]

    def test_explain_code_with_context(self, client: OllamaClient) -> None:
        """Test code explanation with RAG context."""
        client.client.chat = MagicMock(
            return_value={"message": {"content": "explanation"}}
        )

        code = "entity.Save();"
        context = "class Entity { public void Save() { ... } }"

        client.explain_code(code, context=context)

        call_args = client.client.chat.call_args
        user_message = call_args.kwargs["messages"][1]["content"]

        assert "Related Codebase Context" in user_message
        assert context in user_message
        assert code in user_message

    def test_explain_code_with_question(self, client: OllamaClient) -> None:
        """Test code explanation with specific question."""
        client.client.chat = MagicMock(
            return_value={"message": {"content": "answer"}}
        )

        code = "public async Task<int> GetCount() { ... }"
        question = "Why is this method async?"

        client.explain_code(code, question=question)

        call_args = client.client.chat.call_args
        user_message = call_args.kwargs["messages"][1]["content"]

        assert "Specific Question" in user_message
        assert question in user_message

    def test_explain_code_uses_lower_temperature(self, client: OllamaClient) -> None:
        """Test that explain_code uses appropriate temperature."""
        client.client.chat = MagicMock(
            return_value={"message": {"content": "explanation"}}
        )

        client.explain_code("some code")

        call_args = client.client.chat.call_args
        assert call_args.kwargs["options"]["temperature"] == 0.2

    def test_is_available_when_server_running(self, client: OllamaClient) -> None:
        """Test is_available returns True when server is running."""
        client.client.list = MagicMock(return_value=[])

        assert client.is_available() is True

    def test_is_available_when_server_down(self, client: OllamaClient) -> None:
        """Test is_available returns False when server is down."""
        client.client.list = MagicMock(side_effect=Exception("Connection refused"))

        assert client.is_available() is False


class TestOllamaError:
    """Test OllamaError exception."""

    def test_ollama_error_creation(self) -> None:
        """Test creating OllamaError exception."""
        error = OllamaError("Test error message")
        assert str(error) == "Test error message"

    def test_ollama_error_with_cause(self) -> None:
        """Test OllamaError with underlying cause."""
        cause = ValueError("Original error")

        try:
            raise OllamaError("Wrapped error") from cause
        except OllamaError as e:
            assert str(e) == "Wrapped error"
            assert isinstance(e.__cause__, ValueError)
