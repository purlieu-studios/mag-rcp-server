"""Pytest configuration and shared fixtures."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from mag.config import reset_settings


@pytest.fixture(autouse=True)
def reset_config() -> Generator[None, None, None]:
    """Reset configuration singleton before each test."""
    reset_settings()
    yield
    reset_settings()


@pytest.fixture
def temp_codebase(tmp_path: Path) -> Path:
    """Create a temporary codebase directory for testing."""
    codebase_dir = tmp_path / "codebase"
    codebase_dir.mkdir()
    return codebase_dir


@pytest.fixture
def temp_chroma_dir(tmp_path: Path) -> Path:
    """Create a temporary ChromaDB directory for testing."""
    chroma_dir = tmp_path / "chroma"
    chroma_dir.mkdir()
    return chroma_dir


@pytest.fixture
def sample_csharp_file(temp_codebase: Path) -> Path:
    """Create a sample C# file for testing."""
    file_path = temp_codebase / "Sample.cs"
    file_path.write_text(
        '''using System;

namespace TestNamespace
{
    /// <summary>
    /// A sample class for testing.
    /// </summary>
    public class SampleClass
    {
        private int _value;

        /// <summary>
        /// Gets or sets the value.
        /// </summary>
        public int Value
        {
            get => _value;
            set => _value = value;
        }

        /// <summary>
        /// Adds two numbers.
        /// </summary>
        /// <param name="a">First number</param>
        /// <param name="b">Second number</param>
        /// <returns>Sum of a and b</returns>
        public int Add(int a, int b)
        {
            return a + b;
        }

        /// <summary>
        /// Main entry point.
        /// </summary>
        public static void Main(string[] args)
        {
            Console.WriteLine("Hello, World!");
        }
    }
}
''',
        encoding="utf-8",
    )
    return file_path


@pytest.fixture
def sample_csharp_interface(temp_codebase: Path) -> Path:
    """Create a sample C# interface for testing."""
    file_path = temp_codebase / "IRepository.cs"
    file_path.write_text(
        '''namespace TestNamespace
{
    /// <summary>
    /// Generic repository interface.
    /// </summary>
    /// <typeparam name="T">Entity type</typeparam>
    public interface IRepository<T> where T : class
    {
        /// <summary>
        /// Gets entity by ID.
        /// </summary>
        T GetById(int id);

        /// <summary>
        /// Saves an entity.
        /// </summary>
        void Save(T entity);
    }
}
''',
        encoding="utf-8",
    )
    return file_path
