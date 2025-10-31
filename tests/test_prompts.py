"""Tests for MCP prompts."""

import pytest

from mag.prompts.architecture import (
    architecture_analysis_prompt,
    get_architecture_analysis_arguments,
)
from mag.prompts.code_review import code_review_prompt, get_code_review_arguments


class TestCodeReviewPrompt:
    """Test code_review prompt template."""

    def test_code_review_prompt_basic(self) -> None:
        """Test basic code review prompt generation."""
        result = code_review_prompt(
            file_path="EntityManager.cs",
            change_description="Added new CreateEntity method",
        )

        assert isinstance(result, str)
        assert "EntityManager.cs" in result
        assert "Added new CreateEntity method" in result
        assert "search_code" in result

    def test_code_review_prompt_contains_instructions(self) -> None:
        """Test that prompt contains review instructions."""
        result = code_review_prompt(
            file_path="test.cs",
            change_description="test change",
        )

        assert "Review" in result
        assert "architectural concerns" in result.lower()
        assert "performance" in result.lower()
        assert "testing" in result.lower()

    def test_get_code_review_arguments(self) -> None:
        """Test getting code review arguments definition."""
        args = get_code_review_arguments()

        assert isinstance(args, dict)
        assert "file_path" in args
        assert "change_description" in args
        assert args["file_path"]["required"] == "true"
        assert args["change_description"]["required"] == "true"


class TestArchitectureAnalysisPrompt:
    """Test architecture_analysis prompt template."""

    def test_architecture_analysis_prompt_basic(self) -> None:
        """Test basic architecture analysis prompt."""
        result = architecture_analysis_prompt(namespace="GameEngine.Core")

        assert isinstance(result, str)
        assert "GameEngine.Core" in result
        assert "architecture" in result.lower()

    def test_architecture_analysis_prompt_contains_instructions(self) -> None:
        """Test that prompt contains analysis instructions."""
        result = architecture_analysis_prompt(namespace="Test.Namespace")

        assert "list_files" in result
        assert "search_code" in result
        assert "design pattern" in result.lower()
        assert "dependencies" in result.lower()

    def test_architecture_analysis_mentions_mermaid(self) -> None:
        """Test that prompt suggests mermaid diagrams."""
        result = architecture_analysis_prompt(namespace="Core")

        assert "mermaid" in result.lower()

    def test_get_architecture_analysis_arguments(self) -> None:
        """Test getting architecture analysis arguments."""
        args = get_architecture_analysis_arguments()

        assert isinstance(args, dict)
        assert "namespace" in args
        assert args["namespace"]["required"] == "true"
        assert "namespace" in args["namespace"]["description"].lower()
