"""Tests for semantic chunker."""

import pytest

from mag.indexer.chunker import CodeChunk, SemanticChunker
from mag.indexer.parser import CodeNode


class TestSemanticChunker:
    """Test SemanticChunker functionality."""

    @pytest.fixture
    def chunker(self) -> SemanticChunker:
        """Create chunker instance."""
        return SemanticChunker()

    @pytest.fixture
    def small_class_node(self) -> CodeNode:
        """Create a small class node that fits in one chunk."""
        return CodeNode(
            type="class",
            name="SmallClass",
            start_line=1,
            end_line=10,
            code="""public class SmallClass
{
    public int Value { get; set; }

    public void DoSomething()
    {
        Console.WriteLine("Hello");
    }
}""",
            docstring="/// <summary>A small class</summary>",
            file="Small.cs",
            namespace="Test",
        )

    @pytest.fixture
    def method_node(self) -> CodeNode:
        """Create a method node."""
        return CodeNode(
            type="method",
            name="Calculate",
            start_line=15,
            end_line=20,
            code="""public int Calculate(int a, int b)
{
    return a + b;
}""",
            docstring="/// <summary>Calculates sum</summary>",
            parent="Calculator",
            file="Calculator.cs",
            namespace="Math",
        )

    def test_initialization(self, chunker: SemanticChunker) -> None:
        """Test chunker initialization."""
        assert chunker.chunk_size == 512  # default
        assert chunker.overlap == 50  # default
        assert chunker.encoding is not None

    def test_chunk_small_node(
        self,
        chunker: SemanticChunker,
        small_class_node: CodeNode,
    ) -> None:
        """Test chunking a small node that fits in one chunk."""
        chunks = chunker.chunk_nodes([small_class_node])

        assert len(chunks) == 1
        chunk = chunks[0]

        # Content should include context header + code
        assert "// File: Small.cs" in chunk.content
        assert "// Hierarchy: Test.SmallClass" in chunk.content
        assert "A small class" in chunk.content
        assert "public class SmallClass" in chunk.content

        # Metadata
        assert chunk.metadata["file"] == "Small.cs"
        assert chunk.metadata["name"] == "SmallClass"
        assert chunk.metadata["type"] == "class"
        assert chunk.metadata["namespace"] == "Test"
        assert chunk.metadata["hierarchy"] == "Test.SmallClass"
        assert chunk.metadata["lines"] == [1, 10]

        # Token count
        assert chunk.token_count > 0

    def test_chunk_method_node(
        self,
        chunker: SemanticChunker,
        method_node: CodeNode,
    ) -> None:
        """Test chunking a method node."""
        chunks = chunker.chunk_nodes([method_node])

        assert len(chunks) == 1
        chunk = chunks[0]

        assert "// File: Calculator.cs" in chunk.content
        assert "// Hierarchy: Math.Calculator.Calculate" in chunk.content
        assert "Calculates sum" in chunk.content
        assert chunk.metadata["parent"] == "Calculator"
        assert chunk.metadata["hierarchy"] == "Math.Calculator.Calculate"

    def test_multiple_nodes(self, chunker: SemanticChunker) -> None:
        """Test chunking multiple nodes."""
        nodes = [
            CodeNode(
                type="class",
                name="Class1",
                start_line=1,
                end_line=5,
                code="public class Class1 { }",
                file="test.cs",
            ),
            CodeNode(
                type="class",
                name="Class2",
                start_line=7,
                end_line=11,
                code="public class Class2 { }",
                file="test.cs",
            ),
        ]

        chunks = chunker.chunk_nodes(nodes)

        assert len(chunks) == 2
        assert chunks[0].metadata["name"] == "Class1"
        assert chunks[1].metadata["name"] == "Class2"

    def test_node_without_namespace(self, chunker: SemanticChunker) -> None:
        """Test chunking node without namespace."""
        node = CodeNode(
            type="class",
            name="NoNamespace",
            start_line=1,
            end_line=5,
            code="public class NoNamespace { }",
            file="test.cs",
            namespace=None,
        )

        chunks = chunker.chunk_nodes([node])

        assert len(chunks) == 1
        assert "namespace" not in chunks[0].metadata
        assert chunks[0].metadata["hierarchy"] == "NoNamespace"

    def test_node_without_parent(self, chunker: SemanticChunker) -> None:
        """Test chunking node without parent."""
        node = CodeNode(
            type="class",
            name="TopLevel",
            start_line=1,
            end_line=5,
            code="public class TopLevel { }",
            file="test.cs",
            namespace="Test",
        )

        chunks = chunker.chunk_nodes([node])

        assert "parent" not in chunks[0].metadata
        assert chunks[0].metadata["hierarchy"] == "Test.TopLevel"

    def test_node_without_docstring(self, chunker: SemanticChunker) -> None:
        """Test chunking node without docstring."""
        node = CodeNode(
            type="method",
            name="Method",
            start_line=1,
            end_line=3,
            code="public void Method() { }",
            docstring=None,
            file="test.cs",
        )

        chunks = chunker.chunk_nodes([node])

        # Should not include empty docstring lines
        assert chunks[0].content.count("\n") < 5

    def test_large_method_sliding_window(self, chunker: SemanticChunker) -> None:
        """Test sliding window chunking for large methods."""
        # Create a very long method
        long_code_lines = ["public void LongMethod() {"]
        for i in range(200):  # Many lines to exceed chunk size
            long_code_lines.append(f"    Console.WriteLine({i});")
        long_code_lines.append("}")

        node = CodeNode(
            type="method",
            name="LongMethod",
            start_line=1,
            end_line=len(long_code_lines),
            code="\n".join(long_code_lines),
            file="test.cs",
        )

        chunks = chunker.chunk_nodes([node])

        # Should create multiple chunks
        assert len(chunks) > 1

        # All chunks should have the same metadata name
        for chunk in chunks:
            assert chunk.metadata["name"] == "LongMethod"

        # Each chunk should be within token limit
        for chunk in chunks:
            assert chunk.token_count <= chunker.chunk_size

    def test_empty_node_list(self, chunker: SemanticChunker) -> None:
        """Test chunking empty list of nodes."""
        chunks = chunker.chunk_nodes([])
        assert len(chunks) == 0

    def test_hierarchy_construction(self, chunker: SemanticChunker) -> None:
        """Test correct hierarchy construction."""
        test_cases = [
            # (namespace, parent, name, expected_hierarchy)
            ("NS", "Parent", "Child", "NS.Parent.Child"),
            ("NS", None, "Class", "NS.Class"),
            (None, "Parent", "Child", "Parent.Child"),
            (None, None, "Class", "Class"),
        ]

        for namespace, parent, name, expected in test_cases:
            node = CodeNode(
                type="method",
                name=name,
                start_line=1,
                end_line=2,
                code=f"void {name}() {{ }}",
                parent=parent,
                namespace=namespace,
                file="test.cs",
            )

            chunks = chunker.chunk_nodes([node])
            assert chunks[0].metadata["hierarchy"] == expected

    def test_token_counting(self, chunker: SemanticChunker) -> None:
        """Test token counting accuracy."""
        short_text = "Hello"
        long_text = "Hello " * 100

        short_count = chunker._count_tokens(short_text)
        long_count = chunker._count_tokens(long_text)

        assert short_count > 0
        assert long_count > short_count
        assert long_count > 100  # Should be at least 100 tokens

    def test_extract_signature_for_class(self, chunker: SemanticChunker) -> None:
        """Test signature extraction from class code."""
        class_code = """public class MyClass
{
    private int _field;

    public int Property { get; set; }

    public void Method1()
    {
        // Long method body
        for (int i = 0; i < 100; i++)
        {
            Console.WriteLine(i);
        }
    }

    public void Method2()
    {
        // Another method
    }
}"""

        signature = chunker._extract_signature(class_code)

        # Should include class declaration and fields
        assert "public class MyClass" in signature
        assert "_field" in signature

        # Should not include full method bodies
        assert "for (int i = 0;" not in signature or "... methods omitted ..." in signature

    def test_context_header_building(self, chunker: SemanticChunker) -> None:
        """Test building context header for chunks."""
        node = CodeNode(
            type="method",
            name="Test",
            start_line=1,
            end_line=2,
            code="void Test() { }",
            docstring="/// <summary>Test method</summary>",
            parent="TestClass",
            namespace="TestNamespace",
            file="/path/to/file.cs",
        )

        header = chunker._build_context_header(node)

        assert "// File: /path/to/file.cs" in header
        assert "// Hierarchy: TestNamespace.TestClass.Test" in header
        assert "/// <summary>Test method</summary>" in header

    def test_chunk_metadata_completeness(self, chunker: SemanticChunker) -> None:
        """Test that chunk metadata contains all required fields."""
        node = CodeNode(
            type="class",
            name="TestClass",
            start_line=10,
            end_line=20,
            code="public class TestClass { }",
            namespace="NS",
            file="test.cs",
        )

        chunks = chunker.chunk_nodes([node])
        metadata = chunks[0].metadata

        # Required fields
        assert "file" in metadata
        assert "lines" in metadata
        assert "type" in metadata
        assert "name" in metadata
        assert "hierarchy" in metadata

        # Check types
        assert isinstance(metadata["lines"], list)
        assert len(metadata["lines"]) == 2
        assert metadata["lines"][0] == 10
        assert metadata["lines"][1] == 20

    def test_chunking_preserves_code_structure(self, chunker: SemanticChunker) -> None:
        """Test that chunking preserves important code structure."""
        node = CodeNode(
            type="method",
            name="Format",
            start_line=1,
            end_line=5,
            code="""public string Format(string input)
{
    return input.Trim().ToUpper();
}""",
            file="test.cs",
        )

        chunks = chunker.chunk_nodes([node])

        # The actual code should be preserved in the chunk
        assert "return input.Trim().ToUpper();" in chunks[0].content
        assert "public string Format(string input)" in chunks[0].content
