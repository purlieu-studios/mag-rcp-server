"""Tests for C# parser."""

from pathlib import Path

import pytest

from mag.indexer.parser import CodeNode, CSharpParser


class TestCSharpParser:
    """Test CSharpParser functionality."""

    @pytest.fixture
    def parser(self) -> CSharpParser:
        """Create parser instance."""
        return CSharpParser()

    def test_parse_simple_class(self, parser: CSharpParser) -> None:
        """Test parsing a simple class."""
        code = """
namespace TestNamespace
{
    public class SimpleClass
    {
        public void Method() { }
    }
}
"""
        nodes = parser.parse_code(code)

        assert len(nodes) == 2  # class + method
        class_node = nodes[0]
        assert class_node.type == "class"
        assert class_node.name == "SimpleClass"
        assert class_node.namespace == "TestNamespace"
        assert class_node.parent is None

        method_node = nodes[1]
        assert method_node.type == "method"
        assert method_node.name == "Method"
        assert method_node.parent == "SimpleClass"

    def test_parse_class_with_xml_docs(self, parser: CSharpParser) -> None:
        """Test parsing class with XML documentation."""
        code = """
namespace Test
{
    /// <summary>
    /// This is a test class.
    /// </summary>
    public class DocumentedClass
    {
    }
}
"""
        nodes = parser.parse_code(code)

        assert len(nodes) == 1
        class_node = nodes[0]
        assert class_node.docstring is not None
        assert "This is a test class" in class_node.docstring
        assert class_node.docstring.startswith("///")

    def test_parse_interface(self, parser: CSharpParser) -> None:
        """Test parsing an interface."""
        code = """
namespace Test
{
    /// <summary>Interface docs</summary>
    public interface ITestInterface
    {
        void DoSomething();
    }
}
"""
        nodes = parser.parse_code(code)

        interface_node = next(n for n in nodes if n.type == "interface")
        assert interface_node.name == "ITestInterface"
        assert interface_node.namespace == "Test"
        assert "Interface docs" in (interface_node.docstring or "")

    def test_parse_struct(self, parser: CSharpParser) -> None:
        """Test parsing a struct."""
        code = """
public struct Point
{
    public int X;
    public int Y;
}
"""
        nodes = parser.parse_code(code)

        struct_node = next(n for n in nodes if n.type == "struct")
        assert struct_node.name == "Point"

        # Should also extract fields
        field_nodes = [n for n in nodes if n.type == "field"]
        assert len(field_nodes) == 2
        assert {f.name for f in field_nodes} == {"X", "Y"}

    def test_parse_methods_in_class(self, parser: CSharpParser) -> None:
        """Test parsing multiple methods in a class."""
        code = """
public class Calculator
{
    /// <summary>Adds two numbers</summary>
    public int Add(int a, int b)
    {
        return a + b;
    }

    /// <summary>Subtracts two numbers</summary>
    public int Subtract(int a, int b)
    {
        return a - b;
    }
}
"""
        nodes = parser.parse_code(code)

        method_nodes = [n for n in nodes if n.type == "method"]
        assert len(method_nodes) == 2

        add_method = next(m for m in method_nodes if m.name == "Add")
        assert add_method.parent == "Calculator"
        assert "Adds two numbers" in (add_method.docstring or "")

        subtract_method = next(m for m in method_nodes if m.name == "Subtract")
        assert subtract_method.parent == "Calculator"
        assert "Subtracts two numbers" in (subtract_method.docstring or "")

    def test_parse_properties(self, parser: CSharpParser) -> None:
        """Test parsing properties."""
        code = """
public class Person
{
    /// <summary>Gets or sets the name</summary>
    public string Name { get; set; }

    private int _age;

    /// <summary>Gets or sets the age</summary>
    public int Age
    {
        get => _age;
        set => _age = value;
    }
}
"""
        nodes = parser.parse_code(code)

        property_nodes = [n for n in nodes if n.type == "property"]
        assert len(property_nodes) == 2

        assert {p.name for p in property_nodes} == {"Name", "Age"}
        assert all(p.parent == "Person" for p in property_nodes)

    def test_parse_fields(self, parser: CSharpParser) -> None:
        """Test parsing field declarations."""
        code = """
public class DataClass
{
    /// <summary>Counter field</summary>
    private int _counter;

    public string Name, Description;
}
"""
        nodes = parser.parse_code(code)

        field_nodes = [n for n in nodes if n.type == "field"]
        assert len(field_nodes) >= 2

        field_names = {f.name for f in field_nodes}
        assert "_counter" in field_names

    def test_parse_constructor(self, parser: CSharpParser) -> None:
        """Test parsing constructor declarations."""
        code = """
public class MyClass
{
    /// <summary>Constructor</summary>
    public MyClass()
    {
    }
}
"""
        nodes = parser.parse_code(code)

        # Constructors should be extracted as methods
        constructor = next((n for n in nodes if n.type == "method" and "MyClass" in n.code), None)
        assert constructor is not None

    def test_parse_nested_classes(self, parser: CSharpParser) -> None:
        """Test parsing nested classes."""
        code = """
public class Outer
{
    public class Inner
    {
        public void InnerMethod() { }
    }

    public void OuterMethod() { }
}
"""
        nodes = parser.parse_code(code)

        outer_class = next(n for n in nodes if n.name == "Outer" and n.parent is None)
        assert outer_class.type == "class"

        inner_class = next(n for n in nodes if n.name == "Inner")
        assert inner_class.parent == "Outer"

        inner_method = next(n for n in nodes if n.name == "InnerMethod")
        assert inner_method.parent == "Inner"

        outer_method = next(n for n in nodes if n.name == "OuterMethod")
        assert outer_method.parent == "Outer"

    def test_parse_file(
        self,
        parser: CSharpParser,
        sample_csharp_file: Path,
    ) -> None:
        """Test parsing from file."""
        nodes = parser.parse_file(sample_csharp_file)

        assert len(nodes) > 0
        # Should have SampleClass
        class_node = next(n for n in nodes if n.name == "SampleClass")
        assert class_node.type == "class"
        assert class_node.namespace == "TestNamespace"
        assert class_node.file == str(sample_csharp_file)

    def test_parse_file_not_found(self, parser: CSharpParser) -> None:
        """Test parsing non-existent file raises error."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            parser.parse_file(Path("/nonexistent/file.cs"))

    def test_parse_qualified_namespace(self, parser: CSharpParser) -> None:
        """Test parsing qualified namespace names."""
        code = """
namespace Company.Project.Module
{
    public class MyClass { }
}
"""
        nodes = parser.parse_code(code)

        class_node = nodes[0]
        assert class_node.namespace == "Company.Project.Module"

    def test_line_numbers(self, parser: CSharpParser) -> None:
        """Test that line numbers are correctly extracted."""
        code = """namespace Test
{
    public class MyClass
    {
        public void Method()
        {
        }
    }
}"""
        nodes = parser.parse_code(code)

        class_node = next(n for n in nodes if n.type == "class")
        # Class should start around line 3
        assert class_node.start_line >= 2
        assert class_node.end_line > class_node.start_line

        method_node = next(n for n in nodes if n.type == "method")
        assert method_node.start_line >= class_node.start_line
        assert method_node.end_line <= class_node.end_line

    def test_code_content_extraction(self, parser: CSharpParser) -> None:
        """Test that full code is extracted for nodes."""
        code = """
public class TestClass
{
    public int Value { get; set; }
}
"""
        nodes = parser.parse_code(code)

        class_node = nodes[0]
        assert "TestClass" in class_node.code
        assert "public class" in class_node.code

    def test_parse_generic_class(self, parser: CSharpParser) -> None:
        """Test parsing generic classes."""
        code = """
public class Repository<T> where T : class
{
    public T GetById(int id) { return null; }
}
"""
        nodes = parser.parse_code(code)

        class_node = next(n for n in nodes if n.type == "class")
        # tree-sitter might extract "Repository" without the generic part
        assert "Repository" in class_node.name

    def test_parse_interface_with_generic(
        self,
        parser: CSharpParser,
        sample_csharp_interface: Path,
    ) -> None:
        """Test parsing interface with generics from file."""
        nodes = parser.parse_file(sample_csharp_interface)

        interface_node = next((n for n in nodes if n.type == "interface"), None)
        assert interface_node is not None
        assert "IRepository" in interface_node.name

        # Should have methods
        method_nodes = [n for n in nodes if n.type == "method"]
        assert len(method_nodes) >= 2
        method_names = {m.name for m in method_nodes}
        assert "GetById" in method_names
        assert "Save" in method_names

    def test_parse_empty_file(self, parser: CSharpParser) -> None:
        """Test parsing empty file returns no nodes."""
        code = ""
        nodes = parser.parse_code(code)

        assert len(nodes) == 0

    def test_parse_file_without_namespace(self, parser: CSharpParser) -> None:
        """Test parsing file without namespace declaration."""
        code = """
public class NoNamespace
{
    public void Method() { }
}
"""
        nodes = parser.parse_code(code)

        assert len(nodes) == 2
        class_node = nodes[0]
        assert class_node.namespace is None
