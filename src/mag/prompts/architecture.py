"""Architecture analysis prompt template for MCP."""


def architecture_analysis_prompt(namespace: str) -> str:
    """
    Generate an architecture analysis prompt template.

    Args:
        namespace: Namespace to analyze.

    Returns:
        Formatted prompt for architecture analysis.
    """
    return f"""Analyze the architecture of the {namespace} namespace:

Please use the `list_files` and `search_code` tools to:
1. Identify core abstractions and key classes
2. Map dependencies between classes and components
3. Assess design pattern usage and architectural patterns
4. Evaluate separation of concerns and modularity

Then provide:
- **Component diagram** (using mermaid syntax if possible):
  ```mermaid
  graph TD
    A[Component A] --> B[Component B]
  ```

- **Design patterns identified**: List any design patterns in use

- **Architectural assessment**:
  - Strengths of the current architecture
  - Potential improvements or concerns
  - Scalability considerations
  - Maintainability score (1-10) with justification

- **Dependencies**: Key internal and external dependencies

Use the codebase context to provide a comprehensive architectural overview.
"""


def get_architecture_analysis_arguments() -> dict[str, dict[str, str]]:
    """
    Get argument definitions for architecture_analysis prompt.

    Returns:
        Dictionary defining prompt arguments.
    """
    return {
        "namespace": {
            "description": "Namespace to analyze (e.g., 'MyApp.Core')",
            "required": "true",
        },
    }
