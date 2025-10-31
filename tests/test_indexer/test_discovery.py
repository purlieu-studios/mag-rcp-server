"""Tests for file discovery."""

from pathlib import Path

import pytest

from mag.config import Settings
from mag.indexer.discovery import CodebaseDiscovery


class TestCodebaseDiscovery:
    """Test CodebaseDiscovery functionality."""

    @pytest.fixture
    def codebase_with_files(self, temp_codebase: Path) -> Path:
        """Create a test codebase with various files."""
        # Create C# files
        (temp_codebase / "File1.cs").write_text("public class File1 { }")
        (temp_codebase / "File2.cs").write_text("public class File2 { }")

        # Create subdirectories
        subdir = temp_codebase / "src"
        subdir.mkdir()
        (subdir / "File3.cs").write_text("public class File3 { }")

        # Create files to exclude
        obj_dir = temp_codebase / "obj"
        obj_dir.mkdir()
        (obj_dir / "Debug.cs").write_text("// Should be excluded")

        bin_dir = temp_codebase / "bin"
        bin_dir.mkdir()
        (bin_dir / "Release.cs").write_text("// Should be excluded")

        # Create non-C# files
        (temp_codebase / "README.md").write_text("# README")
        (temp_codebase / "data.json").write_text("{}")

        return temp_codebase

    def test_initialization_with_default_path(self) -> None:
        """Test initialization with path from settings."""
        discovery = CodebaseDiscovery()
        assert discovery.root_path.exists()

    def test_initialization_with_custom_path(self, temp_codebase: Path) -> None:
        """Test initialization with custom path."""
        discovery = CodebaseDiscovery(root_path=temp_codebase)
        assert discovery.root_path == temp_codebase

    def test_initialization_with_nonexistent_path(self, tmp_path: Path) -> None:
        """Test initialization fails for nonexistent path."""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(ValueError, match="does not exist"):
            CodebaseDiscovery(root_path=nonexistent)

    def test_discover_files_basic(self, codebase_with_files: Path) -> None:
        """Test basic file discovery."""
        discovery = CodebaseDiscovery(root_path=codebase_with_files)
        files = discovery.discover_files()

        # Should find only .cs files not in obj/bin
        cs_files = [f.name for f in files]
        assert "File1.cs" in cs_files
        assert "File2.cs" in cs_files
        assert "File3.cs" in cs_files

        # Should not include excluded directories
        assert not any("obj" in str(f) for f in files)
        assert not any("bin" in str(f) for f in files)

        # Should not include non-C# files
        assert not any(f.suffix == ".md" for f in files)
        assert not any(f.suffix == ".json" for f in files)

    def test_discover_files_returns_sorted(self, codebase_with_files: Path) -> None:
        """Test that discovered files are sorted."""
        discovery = CodebaseDiscovery(root_path=codebase_with_files)
        files = discovery.discover_files()

        # Should be sorted
        assert files == sorted(files)

    def test_file_extension_filtering(self, temp_codebase: Path) -> None:
        """Test filtering by file extension."""
        (temp_codebase / "test.cs").write_text("code")
        (temp_codebase / "test.csx").write_text("script")
        (temp_codebase / "test.txt").write_text("text")

        # Default extensions
        discovery = CodebaseDiscovery(root_path=temp_codebase)
        files = discovery.discover_files()

        assert len(files) == 1  # Only .cs by default
        assert files[0].suffix == ".cs"

    def test_exclude_patterns_default(self, temp_codebase: Path) -> None:
        """Test default exclude patterns."""
        # Create files in excluded directories
        for excluded_dir in ["obj", "bin", "packages", ".vs"]:
            dir_path = temp_codebase / excluded_dir / "nested"
            dir_path.mkdir(parents=True)
            (dir_path / "test.cs").write_text("code")

        # Create file in included directory
        (temp_codebase / "src" / "test.cs").parent.mkdir()
        (temp_codebase / "src" / "test.cs").write_text("code")

        discovery = CodebaseDiscovery(root_path=temp_codebase)
        files = discovery.discover_files()

        # Should only find the file in src
        assert len(files) == 1
        assert "src" in str(files[0])

    def test_gitignore_integration(self, temp_codebase: Path) -> None:
        """Test .gitignore file integration."""
        # Initialize git repo
        import git

        repo = git.Repo.init(temp_codebase)

        # Create .gitignore
        gitignore = temp_codebase / ".gitignore"
        gitignore.write_text("ignored/\n*.ignore.cs\n")

        # Create files
        (temp_codebase / "normal.cs").write_text("code")

        ignored_dir = temp_codebase / "ignored"
        ignored_dir.mkdir()
        (ignored_dir / "should_ignore.cs").write_text("code")

        (temp_codebase / "test.ignore.cs").write_text("code")

        discovery = CodebaseDiscovery(root_path=temp_codebase)
        files = discovery.discover_files()

        file_names = [f.name for f in files]

        # Should find normal file
        assert "normal.cs" in file_names

        # Should respect .gitignore
        assert "should_ignore.cs" not in file_names
        assert "test.ignore.cs" not in file_names

    def test_non_git_repository(self, temp_codebase: Path) -> None:
        """Test discovery works without git repository."""
        (temp_codebase / "test.cs").write_text("code")

        # Should not raise error for non-git directory
        discovery = CodebaseDiscovery(root_path=temp_codebase)
        files = discovery.discover_files()

        assert len(files) == 1

    def test_nested_directory_structure(self, temp_codebase: Path) -> None:
        """Test discovery in deeply nested directories."""
        deep_path = temp_codebase / "a" / "b" / "c" / "d"
        deep_path.mkdir(parents=True)
        (deep_path / "deep.cs").write_text("code")

        discovery = CodebaseDiscovery(root_path=temp_codebase)
        files = discovery.discover_files()

        assert len(files) == 1
        assert files[0].name == "deep.cs"

    def test_get_stats(self, codebase_with_files: Path) -> None:
        """Test getting discovery statistics."""
        discovery = CodebaseDiscovery(root_path=codebase_with_files)
        stats = discovery.get_stats()

        assert "total_files" in stats
        assert "file_extensions" in stats
        assert "total_size_bytes" in stats

        assert stats["total_files"] > 0
        assert ".cs" in stats["file_extensions"]
        assert stats["total_size_bytes"] > 0

    def test_empty_codebase(self, temp_codebase: Path) -> None:
        """Test discovery in empty codebase."""
        discovery = CodebaseDiscovery(root_path=temp_codebase)
        files = discovery.discover_files()

        assert len(files) == 0

    def test_symlink_handling(self, temp_codebase: Path) -> None:
        """Test that symlinks are handled correctly."""
        # Create a real file
        (temp_codebase / "real.cs").write_text("code")

        # Create a symlink
        symlink = temp_codebase / "link.cs"
        try:
            symlink.symlink_to(temp_codebase / "real.cs")
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        discovery = CodebaseDiscovery(root_path=temp_codebase)
        files = discovery.discover_files()

        # Depending on implementation, may include both or just real file
        assert len(files) >= 1

    def test_unicode_filenames(self, temp_codebase: Path) -> None:
        """Test handling of unicode in filenames."""
        unicode_file = temp_codebase / "测试.cs"
        unicode_file.write_text("code", encoding="utf-8")

        discovery = CodebaseDiscovery(root_path=temp_codebase)
        files = discovery.discover_files()

        assert len(files) == 1
        assert files[0].name == "测试.cs"

    def test_custom_exclude_patterns(self, temp_codebase: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test using custom exclude patterns."""
        monkeypatch.setenv("MAG_EXCLUDE_PATTERNS", '["**/custom/**"]')

        (temp_codebase / "normal.cs").write_text("code")

        custom_dir = temp_codebase / "custom"
        custom_dir.mkdir()
        (custom_dir / "excluded.cs").write_text("code")

        # Need to reload settings
        from mag.config import reset_settings

        reset_settings()

        discovery = CodebaseDiscovery(root_path=temp_codebase)
        files = discovery.discover_files()

        file_names = [f.name for f in files]
        assert "normal.cs" in file_names
        assert "excluded.cs" not in file_names

    def test_file_outside_root_path(self, temp_codebase: Path, tmp_path: Path) -> None:
        """Test that files outside root path are rejected."""
        discovery = CodebaseDiscovery(root_path=temp_codebase)

        # Create file outside root
        outside_file = tmp_path / "outside.cs"
        outside_file.write_text("code")

        # Should return False for file outside root
        assert not discovery._should_index_file(outside_file)
