"""C# code parser using tree-sitter."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from tree_sitter import Language, Parser, Tree
from tree_sitter_c_sharp import language


CodeNodeType = Literal["class", "interface", "struct", "method", "property", "field"]


@dataclass
class CodeNode:
    """Represents a parsed code element."""

    type: CodeNodeType
    name: str
    start_line: int
    end_line: int
    code: str
    docstring: str | None = None
    parent: str | None = None
    file: str | None = None
    namespace: str | None = None


class CSharpParser:
    """Parser for C# code using tree-sitter."""

    def __init__(self) -> None:
        """Initialize the C# parser."""
        self.parser = Parser(Language(language()))

    def parse_file(self, file_path: Path) -> list[CodeNode]:
        """
        Parse a C# file and extract code nodes.

        Args:
            file_path: Path to the C# file.

        Returns:
            List of extracted code nodes.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file cannot be parsed.
        """
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise FileNotFoundError(msg)

        try:
            source_code = file_path.read_bytes()
        except Exception as e:
            msg = f"Failed to read file {file_path}: {e}"
            raise ValueError(msg) from e

        tree = self.parser.parse(source_code)
        nodes: list[CodeNode] = []

        # Extract namespace first
        namespace = self._extract_namespace(tree.root_node, source_code)

        # Extract all code nodes
        self._traverse_tree(
            tree.root_node,
            source_code,
            nodes,
            str(file_path),
            namespace,
        )

        return nodes

    def parse_code(self, source_code: str, file_path: str = "<string>") -> list[CodeNode]:
        """
        Parse C# source code string.

        Args:
            source_code: C# source code as string.
            file_path: Optional file path for context.

        Returns:
            List of extracted code nodes.
        """
        tree = self.parser.parse(source_code.encode("utf-8"))
        nodes: list[CodeNode] = []

        source_bytes = source_code.encode("utf-8")
        namespace = self._extract_namespace(tree.root_node, source_bytes)

        self._traverse_tree(
            tree.root_node,
            source_bytes,
            nodes,
            file_path,
            namespace,
        )

        return nodes

    def _extract_namespace(self, node: object, source: bytes) -> str | None:
        """Extract namespace from the tree."""
        namespace_node = self._find_first_child_of_type(node, "namespace_declaration")
        if namespace_node:
            name_node = self._find_first_child_of_type(namespace_node, "qualified_name")
            if not name_node:
                name_node = self._find_first_child_of_type(namespace_node, "identifier")
            if name_node:
                return self._get_node_text(name_node, source)
        return None

    def _traverse_tree(
        self,
        node: object,
        source: bytes,
        nodes: list[CodeNode],
        file_path: str,
        namespace: str | None,
        parent: str | None = None,
    ) -> None:
        """Recursively traverse AST and extract code nodes."""
        node_type = getattr(node, "type", None)

        # Check if this is a node we want to extract
        if node_type == "class_declaration":
            code_node = self._extract_class(node, source, file_path, namespace, parent)
            nodes.append(code_node)
            # Traverse children with this class as parent
            for child in getattr(node, "children", []):
                self._traverse_tree(
                    child,
                    source,
                    nodes,
                    file_path,
                    namespace,
                    code_node.name,
                )
        elif node_type == "interface_declaration":
            code_node = self._extract_interface(node, source, file_path, namespace, parent)
            nodes.append(code_node)
            for child in getattr(node, "children", []):
                self._traverse_tree(child, source, nodes, file_path, namespace, code_node.name)
        elif node_type == "struct_declaration":
            code_node = self._extract_struct(node, source, file_path, namespace, parent)
            nodes.append(code_node)
            for child in getattr(node, "children", []):
                self._traverse_tree(child, source, nodes, file_path, namespace, code_node.name)
        elif node_type == "method_declaration" or node_type == "constructor_declaration":
            code_node = self._extract_method(node, source, file_path, namespace, parent)
            nodes.append(code_node)
        elif node_type == "property_declaration":
            code_node = self._extract_property(node, source, file_path, namespace, parent)
            nodes.append(code_node)
        elif node_type == "field_declaration":
            # Extract each field from the declaration
            for field_node in self._extract_fields(node, source, file_path, namespace, parent):
                nodes.append(field_node)
        else:
            # Continue traversing for other node types
            for child in getattr(node, "children", []):
                self._traverse_tree(child, source, nodes, file_path, namespace, parent)

    def _extract_class(
        self,
        node: object,
        source: bytes,
        file_path: str,
        namespace: str | None,
        parent: str | None,
    ) -> CodeNode:
        """Extract class declaration."""
        name = self._get_node_name(node, source)
        docstring = self._extract_docstring(node, source)

        return CodeNode(
            type="class",
            name=name,
            start_line=getattr(node, "start_point", (0, 0))[0] + 1,
            end_line=getattr(node, "end_point", (0, 0))[0] + 1,
            code=self._get_node_text(node, source),
            docstring=docstring,
            parent=parent,
            file=file_path,
            namespace=namespace,
        )

    def _extract_interface(
        self,
        node: object,
        source: bytes,
        file_path: str,
        namespace: str | None,
        parent: str | None,
    ) -> CodeNode:
        """Extract interface declaration."""
        name = self._get_node_name(node, source)
        docstring = self._extract_docstring(node, source)

        return CodeNode(
            type="interface",
            name=name,
            start_line=getattr(node, "start_point", (0, 0))[0] + 1,
            end_line=getattr(node, "end_point", (0, 0))[0] + 1,
            code=self._get_node_text(node, source),
            docstring=docstring,
            parent=parent,
            file=file_path,
            namespace=namespace,
        )

    def _extract_struct(
        self,
        node: object,
        source: bytes,
        file_path: str,
        namespace: str | None,
        parent: str | None,
    ) -> CodeNode:
        """Extract struct declaration."""
        name = self._get_node_name(node, source)
        docstring = self._extract_docstring(node, source)

        return CodeNode(
            type="struct",
            name=name,
            start_line=getattr(node, "start_point", (0, 0))[0] + 1,
            end_line=getattr(node, "end_point", (0, 0))[0] + 1,
            code=self._get_node_text(node, source),
            docstring=docstring,
            parent=parent,
            file=file_path,
            namespace=namespace,
        )

    def _extract_method(
        self,
        node: object,
        source: bytes,
        file_path: str,
        namespace: str | None,
        parent: str | None,
    ) -> CodeNode:
        """Extract method or constructor declaration."""
        name = self._get_node_name(node, source)
        docstring = self._extract_docstring(node, source)

        return CodeNode(
            type="method",
            name=name,
            start_line=getattr(node, "start_point", (0, 0))[0] + 1,
            end_line=getattr(node, "end_point", (0, 0))[0] + 1,
            code=self._get_node_text(node, source),
            docstring=docstring,
            parent=parent,
            file=file_path,
            namespace=namespace,
        )

    def _extract_property(
        self,
        node: object,
        source: bytes,
        file_path: str,
        namespace: str | None,
        parent: str | None,
    ) -> CodeNode:
        """Extract property declaration."""
        name = self._get_node_name(node, source)
        docstring = self._extract_docstring(node, source)

        return CodeNode(
            type="property",
            name=name,
            start_line=getattr(node, "start_point", (0, 0))[0] + 1,
            end_line=getattr(node, "end_point", (0, 0))[0] + 1,
            code=self._get_node_text(node, source),
            docstring=docstring,
            parent=parent,
            file=file_path,
            namespace=namespace,
        )

    def _extract_fields(
        self,
        node: object,
        source: bytes,
        file_path: str,
        namespace: str | None,
        parent: str | None,
    ) -> list[CodeNode]:
        """Extract field declarations (may have multiple variables)."""
        docstring = self._extract_docstring(node, source)
        fields = []

        # Field declarations can have multiple variable declarators
        for child in getattr(node, "children", []):
            if getattr(child, "type", None) == "variable_declaration":
                for var_child in getattr(child, "children", []):
                    if getattr(var_child, "type", None) == "variable_declarator":
                        name_node = self._find_first_child_of_type(var_child, "identifier")
                        if name_node:
                            name = self._get_node_text(name_node, source)
                            fields.append(
                                CodeNode(
                                    type="field",
                                    name=name,
                                    start_line=getattr(node, "start_point", (0, 0))[0] + 1,
                                    end_line=getattr(node, "end_point", (0, 0))[0] + 1,
                                    code=self._get_node_text(node, source),
                                    docstring=docstring,
                                    parent=parent,
                                    file=file_path,
                                    namespace=namespace,
                                )
                            )

        return fields if fields else []

    def _get_node_name(self, node: object, source: bytes) -> str:
        """Extract the name identifier from a node."""
        name_node = self._find_first_child_of_type(node, "identifier")
        if name_node:
            return self._get_node_text(name_node, source)
        return "<unnamed>"

    def _find_first_child_of_type(self, node: object, node_type: str) -> object | None:
        """Find the first child node of a specific type."""
        for child in getattr(node, "children", []):
            if getattr(child, "type", None) == node_type:
                return child
        return None

    def _get_node_text(self, node: object, source: bytes) -> str:
        """Get the text content of a node."""
        start_byte = getattr(node, "start_byte", 0)
        end_byte = getattr(node, "end_byte", 0)
        return source[start_byte:end_byte].decode("utf-8", errors="replace")

    def _extract_docstring(self, node: object, source: bytes) -> str | None:
        """Extract XML documentation comment preceding a node."""
        # Look for comment nodes before this node
        prev_sibling = getattr(node, "prev_sibling", None)

        comments = []
        current = prev_sibling

        # Traverse backwards to collect consecutive comments
        while current is not None:
            node_type = getattr(current, "type", None)
            if node_type == "comment":
                comment_text = self._get_node_text(current, source)
                # Check if it's an XML doc comment
                if comment_text.strip().startswith("///"):
                    comments.insert(0, comment_text.strip())
                    current = getattr(current, "prev_sibling", None)
                else:
                    break
            elif node_type in ("attribute_list", "modifiers"):
                # Skip attributes and modifiers
                current = getattr(current, "prev_sibling", None)
            else:
                break

        if comments:
            return "\n".join(comments)
        return None
