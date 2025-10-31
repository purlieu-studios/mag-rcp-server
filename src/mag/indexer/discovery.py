"""File discovery for codebase indexing."""

from pathlib import Path

import git
import pathspec

from mag.config import get_settings


class CodebaseDiscovery:
    """Discovers files in a codebase for indexing."""

    def __init__(self, root_path: Path | None = None) -> None:
        """
        Initialize codebase discovery.

        Args:
            root_path: Root directory of the codebase. If None, uses settings.
        """
        settings = get_settings()
        self.root_path = root_path or settings.codebase_root
        self.file_extensions = settings.file_extensions
        self.exclude_patterns = settings.exclude_patterns

        if not self.root_path.exists():
            msg = f"Codebase root does not exist: {self.root_path}"
            raise ValueError(msg)

        # Load .gitignore patterns if available
        self.gitignore_spec = self._load_gitignore()

    def discover_files(self) -> list[Path]:
        """
        Discover all indexable files in the codebase.

        Returns:
            List of Path objects for files to index.
        """
        discovered_files: list[Path] = []

        for file_path in self.root_path.rglob("*"):
            if self._should_index_file(file_path):
                discovered_files.append(file_path)

        return sorted(discovered_files)

    def _should_index_file(self, file_path: Path) -> bool:
        """
        Check if a file should be indexed.

        Args:
            file_path: Path to check.

        Returns:
            True if file should be indexed, False otherwise.
        """
        # Must be a file
        if not file_path.is_file():
            return False

        # Check file extension
        if not any(file_path.suffix == ext for ext in self.file_extensions):
            return False

        # Get relative path for pattern matching
        try:
            rel_path = file_path.relative_to(self.root_path)
        except ValueError:
            return False

        rel_path_str = rel_path.as_posix()

        # Check exclude patterns
        if self._matches_exclude_pattern(rel_path_str):
            return False

        # Check gitignore
        if self.gitignore_spec and self.gitignore_spec.match_file(rel_path_str):
            return False

        return True

    def _matches_exclude_pattern(self, path: str) -> bool:
        """
        Check if path matches any exclude pattern.

        Args:
            path: Relative path as string (POSIX style).

        Returns:
            True if path matches exclude pattern, False otherwise.
        """
        exclude_spec = pathspec.PathSpec.from_lines("gitwildmatch", self.exclude_patterns)
        return exclude_spec.match_file(path)

    def _load_gitignore(self) -> pathspec.PathSpec | None:
        """
        Load .gitignore patterns from the repository.

        Returns:
            PathSpec object with gitignore patterns, or None if not a git repo.
        """
        try:
            repo = git.Repo(self.root_path, search_parent_directories=True)
            gitignore_path = Path(repo.working_dir) / ".gitignore"

            if gitignore_path.exists():
                patterns = gitignore_path.read_text(encoding="utf-8").splitlines()
                # Filter out comments and empty lines
                patterns = [
                    p.strip()
                    for p in patterns
                    if p.strip() and not p.strip().startswith("#")
                ]
                return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        except (git.InvalidGitRepositoryError, git.NoSuchPathError):
            # Not a git repository, that's fine
            pass

        return None

    def get_stats(self) -> dict[str, int | list[str]]:
        """
        Get statistics about discoverable files.

        Returns:
            Dictionary with discovery statistics.
        """
        files = self.discover_files()

        return {
            "total_files": len(files),
            "file_extensions": list(set(f.suffix for f in files)),
            "total_size_bytes": sum(f.stat().st_size for f in files),
        }
