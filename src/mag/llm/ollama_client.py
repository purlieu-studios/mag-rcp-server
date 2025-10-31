"""Ollama client for embeddings and code explanations."""

from typing import Any

import ollama

from mag.config import get_settings


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, host: str | None = None) -> None:
        """
        Initialize Ollama client.

        Args:
            host: Ollama API host URL. If None, uses settings.
        """
        settings = get_settings()
        self.host = host or settings.ollama_host
        self.embedding_model = settings.embedding_model
        self.llm_model = settings.llm_model
        self.client = ollama.Client(host=self.host)

    def embed(self, text: str) -> list[float]:
        """
        Generate embeddings for text using Ollama.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector as list of floats.

        Raises:
            OllamaError: If embedding generation fails.
        """
        try:
            response = self.client.embeddings(
                model=self.embedding_model,
                prompt=text,
            )
            return response["embedding"]
        except Exception as e:
            msg = f"Failed to generate embedding: {e}"
            raise OllamaError(msg) from e

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.

        Raises:
            OllamaError: If embedding generation fails.
        """
        return [self.embed(text) for text in texts]

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate text completion using Ollama LLM.

        Args:
            prompt: The prompt to send to the model.
            system: Optional system message to set context.
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text response.

        Raises:
            OllamaError: If generation fails.
        """
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat(
                model=self.llm_model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )
            return response["message"]["content"]
        except Exception as e:
            msg = f"Failed to generate completion: {e}"
            raise OllamaError(msg) from e

    def explain_code(
        self,
        code: str,
        context: str | None = None,
        question: str | None = None,
    ) -> str:
        """
        Generate an explanation for code using RAG context.

        Args:
            code: The code to explain.
            context: Additional context from codebase (RAG results).
            question: Specific question about the code.

        Returns:
            Explanation of the code.

        Raises:
            OllamaError: If explanation generation fails.
        """
        system = (
            "You are an expert C# developer. Analyze the provided code and "
            "explain it clearly and concisely. Focus on:\n"
            "- What the code does\n"
            "- Key design patterns or techniques used\n"
            "- Potential issues or improvements\n"
            "- How it fits into the broader codebase"
        )

        prompt_parts = []

        if context:
            prompt_parts.append(f"# Related Codebase Context\n{context}\n")

        prompt_parts.append(f"# Code to Explain\n```csharp\n{code}\n```\n")

        if question:
            prompt_parts.append(f"# Specific Question\n{question}\n")
        else:
            prompt_parts.append("Provide a comprehensive explanation of this code.")

        prompt = "\n".join(prompt_parts)

        return self.generate(prompt, system=system, temperature=0.2)

    def is_available(self) -> bool:
        """
        Check if Ollama server is available.

        Returns:
            True if server is reachable, False otherwise.
        """
        try:
            self.client.list()
            return True
        except Exception:
            return False


class OllamaError(Exception):
    """Exception raised for Ollama-related errors."""

    pass
