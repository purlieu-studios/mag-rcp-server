"""Code review prompt template for MCP."""


def code_review_prompt(file_path: str, change_description: str) -> str:
    """
    Generate a code review prompt template.

    Args:
        file_path: Path to the file being reviewed.
        change_description: Description of what changed.

    Returns:
        Formatted prompt for code review.
    """
    return f"""Review the following C# code change in {file_path}:

Change: {change_description}

Please use the `search_code` tool to:
1. Find related classes and methods in the codebase
2. Identify potential breaking changes
3. Check for style consistency with existing patterns

Then provide:
- **Architectural concerns**: How does this change fit into the overall design?
- **Performance implications**: Are there any performance considerations?
- **Testing recommendations**: What tests should be added or updated?
- **Related code**: What other parts of the codebase might be affected?

Use the codebase context to provide specific, actionable feedback.
"""


def get_code_review_arguments() -> dict[str, dict[str, str]]:
    """
    Get argument definitions for code_review prompt.

    Returns:
        Dictionary defining prompt arguments.
    """
    return {
        "file_path": {
            "description": "Path to file being reviewed",
            "required": "true",
        },
        "change_description": {
            "description": "Description of what changed in the code",
            "required": "true",
        },
    }
