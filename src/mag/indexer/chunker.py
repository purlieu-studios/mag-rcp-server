"""Semantic code chunking for embedding."""

from dataclasses import dataclass

import tiktoken

from mag.config import get_settings
from mag.indexer.parser import CodeNode


@dataclass
class CodeChunk:
    """Represents a chunk of code ready for embedding."""

    content: str
    metadata: dict[str, str | int | list[int]]
    token_count: int


class SemanticChunker:
    """Chunks code semantically for vector embeddings."""

    def __init__(self) -> None:
        """Initialize the chunker."""
        settings = get_settings()
        self.chunk_size = settings.chunk_size_tokens
        self.overlap = settings.chunk_overlap_tokens

        # Use tiktoken for token counting (cl100k_base for general text)
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # Fallback if tiktoken not available
            self.encoding = None

    def chunk_nodes(self, nodes: list[CodeNode]) -> list[CodeChunk]:
        """
        Convert code nodes into chunks ready for embedding.

        Args:
            nodes: List of parsed code nodes.

        Returns:
            List of code chunks with metadata.
        """
        chunks: list[CodeChunk] = []

        for node in nodes:
            node_chunks = self._chunk_node(node)
            chunks.extend(node_chunks)

        return chunks

    def _chunk_node(self, node: CodeNode) -> list[CodeChunk]:
        """
        Chunk a single code node.

        Args:
            node: Code node to chunk.

        Returns:
            List of chunks for this node.
        """
        # Build context header
        context_header = self._build_context_header(node)

        # Combine header with code
        full_content = f"{context_header}\n{node.code}"

        # Count tokens
        token_count = self._count_tokens(full_content)

        # If fits in one chunk, return as-is
        if token_count <= self.chunk_size:
            return [self._create_chunk(full_content, node, token_count)]

        # For large nodes, need to split
        return self._split_large_node(node, context_header)

    def _build_context_header(self, node: CodeNode) -> str:
        """
        Build context header for a code chunk.

        Args:
            node: Code node.

        Returns:
            Context header string.
        """
        parts = []

        # File information
        if node.file:
            parts.append(f"// File: {node.file}")

        # Hierarchy information
        if node.parent:
            if node.namespace:
                hierarchy = f"{node.namespace}.{node.parent}.{node.name}"
            else:
                hierarchy = f"{node.parent}.{node.name}"
            parts.append(f"// Hierarchy: {hierarchy}")
        elif node.namespace:
            hierarchy = f"{node.namespace}.{node.name}"
            parts.append(f"// Hierarchy: {hierarchy}")

        # Docstring
        if node.docstring:
            parts.append(node.docstring)

        return "\n".join(parts)

    def _create_chunk(
        self,
        content: str,
        node: CodeNode,
        token_count: int | None = None,
    ) -> CodeChunk:
        """
        Create a code chunk with metadata.

        Args:
            content: Chunk content.
            node: Source code node.
            token_count: Pre-calculated token count, if available.

        Returns:
            CodeChunk object.
        """
        if token_count is None:
            token_count = self._count_tokens(content)

        # Build hierarchy
        hierarchy_parts = []
        if node.namespace:
            hierarchy_parts.append(node.namespace)
        if node.parent:
            hierarchy_parts.append(node.parent)
        hierarchy_parts.append(node.name)
        hierarchy = ".".join(hierarchy_parts)

        metadata = {
            "file": node.file or "",
            "lines": [node.start_line, node.end_line],
            "type": node.type,
            "name": node.name,
            "hierarchy": hierarchy,
        }

        if node.parent:
            metadata["parent"] = node.parent

        if node.namespace:
            metadata["namespace"] = node.namespace

        return CodeChunk(
            content=content,
            metadata=metadata,
            token_count=token_count,
        )

    def _split_large_node(self, node: CodeNode, context_header: str) -> list[CodeChunk]:
        """
        Split a large code node into multiple chunks.

        For classes, split into signature + methods.
        For large methods, use sliding window.

        Args:
            node: Large code node.
            context_header: Context header to include.

        Returns:
            List of chunks.
        """
        chunks: list[CodeChunk] = []

        if node.type in ("class", "interface", "struct"):
            # For classes/interfaces, create signature chunk
            signature = self._extract_signature(node.code)
            signature_content = f"{context_header}\n{signature}"

            if self._count_tokens(signature_content) <= self.chunk_size:
                chunks.append(
                    self._create_chunk(signature_content, node)
                )

            # Methods and properties will be chunked separately
            # (they're separate nodes in the parse tree)
        else:
            # For large methods/properties, use sliding window
            chunks.extend(self._sliding_window_chunk(node, context_header))

        return chunks if chunks else [self._create_chunk(f"{context_header}\n{node.code}", node)]

    def _extract_signature(self, code: str) -> str:
        """
        Extract class/interface signature (declaration + fields, without method bodies).

        Args:
            code: Full code string.

        Returns:
            Signature portion of the code.
        """
        lines = code.splitlines()
        signature_lines = []
        brace_count = 0
        in_method = False
        prev_line_method_signature = False

        for line in lines:
            stripped = line.strip()

            # Check if previous line was a method signature (has `(` but no `{`)
            # and current line is just an opening brace
            if prev_line_method_signature and stripped == "{":
                in_method = True
                prev_line_method_signature = False

            # Check if this looks like a method signature line
            if (
                "(" in line
                and ")" in line
                and not in_method
                and brace_count >= 1
                and any(keyword in line for keyword in ["void ", "int ", "string ", "public ", "private ", "protected ", "bool ", "double ", "float "])
            ):
                # Check if opening brace is NOT on this line
                if "{" not in line:
                    prev_line_method_signature = True
                    signature_lines.append(line)
                    continue
                else:
                    # Opening brace is on the same line
                    in_method = True

            # Track braces
            brace_count += line.count("{") - line.count("}")

            # Include line if we're not in a method body, or if we're at class level (brace_count == 1)
            if not in_method:
                signature_lines.append(line)
            elif brace_count == 1 and "}" in line:
                # Exiting a method
                in_method = False
                signature_lines.append("    // ... method body omitted ...")
                signature_lines.append(line)

        return "\n".join(signature_lines)

    def _sliding_window_chunk(self, node: CodeNode, context_header: str) -> list[CodeChunk]:
        """
        Create chunks using sliding window approach.

        Args:
            node: Code node to chunk.
            context_header: Context header.

        Returns:
            List of chunks.
        """
        chunks: list[CodeChunk] = []
        lines = node.code.splitlines()

        if not lines:
            return chunks

        # Calculate lines per chunk
        # Estimate roughly: chunk_size tokens ≈ chunk_size * 0.75 chars ≈ chunk_size * 0.15 lines
        # This is a rough heuristic
        est_lines_per_chunk = max(5, self.chunk_size // 6)
        overlap_lines = max(1, self.overlap // 6)

        start_idx = 0
        while start_idx < len(lines):
            end_idx = min(start_idx + est_lines_per_chunk, len(lines))

            chunk_lines = lines[start_idx:end_idx]
            chunk_code = "\n".join(chunk_lines)
            chunk_content = f"{context_header}\n{chunk_code}"

            # Adjust if over token limit
            token_count = self._count_tokens(chunk_content)
            while token_count > self.chunk_size and len(chunk_lines) > 1:
                chunk_lines = chunk_lines[:-1]
                chunk_code = "\n".join(chunk_lines)
                chunk_content = f"{context_header}\n{chunk_code}"
                token_count = self._count_tokens(chunk_content)

            if chunk_lines:
                chunks.append(self._create_chunk(chunk_content, node, token_count))

            # Move window forward with overlap
            start_idx = end_idx - overlap_lines
            if start_idx >= len(lines) - overlap_lines:
                break

        return chunks

    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for.

        Returns:
            Token count.
        """
        if self.encoding:
            return len(self.encoding.encode(text))

        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(text) // 4
