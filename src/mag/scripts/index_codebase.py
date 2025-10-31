"""CLI script for indexing codebases."""

import argparse
import logging
import sys
from pathlib import Path

from mag.config import get_settings
from mag.indexer.embedder import CodebaseEmbedder
from mag.llm.ollama_client import OllamaClient


def setup_logging(verbose: bool) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def progress_callback(message: str, current: int, total: int) -> None:
    """Print progress updates."""
    percentage = (current / total * 100) if total > 0 else 0
    print(f"[{current}/{total}] ({percentage:.1f}%) {message}")


def main() -> int:
    """Main entry point for indexing CLI."""
    parser = argparse.ArgumentParser(
        description="Index a C# codebase for semantic search",
    )

    parser.add_argument(
        "--codebase",
        type=Path,
        help="Path to codebase root (default: from config)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing index before indexing",
    )
    parser.add_argument(
        "--check-ollama",
        action="store_true",
        help="Check Ollama availability and exit",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show index statistics and exit",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger("mag.cli")

    settings = get_settings()

    # Update codebase root if provided
    if args.codebase:
        import os

        os.environ["MAG_CODEBASE_ROOT"] = str(args.codebase)
        from mag.config import reset_settings

        reset_settings()
        settings = get_settings()

    # Check Ollama availability
    if args.check_ollama:
        print("Checking Ollama connection...")
        ollama_client = OllamaClient()

        if ollama_client.is_available():
            print(f"✓ Ollama is available at {settings.ollama_host}")
            print(f"  Embedding model: {settings.embedding_model}")
            print(f"  LLM model: {settings.llm_model}")
            return 0
        else:
            print(f"✗ Cannot connect to Ollama at {settings.ollama_host}")
            print("  Please ensure Ollama is running:")
            print("  - Install: https://ollama.ai/download")
            print(f"  - Pull models: ollama pull {settings.embedding_model}")
            return 1

    # Show statistics
    if args.stats:
        embedder = CodebaseEmbedder()
        stats = embedder.get_index_stats()

        print("\n=== Index Statistics ===")
        print(f"Total chunks: {stats.get('total_chunks', 0)}")
        print(f"Code types: {', '.join(stats.get('code_types', []))}")
        print(f"Collection: {stats.get('collection_name', 'N/A')}")
        print()

        return 0

    # Perform indexing
    print(f"\n=== MAG Codebase Indexing ===")
    print(f"Codebase: {settings.codebase_root}")
    print(f"ChromaDB: {settings.chroma_persist_dir}")
    print(f"Ollama: {settings.ollama_host}")
    print()

    # Initialize embedder
    embedder = CodebaseEmbedder()

    # Check Ollama
    logger.info("Checking Ollama availability...")
    if not embedder.ollama_client.is_available():
        logger.error("Cannot connect to Ollama. Please ensure it's running.")
        return 1

    # Clear index if requested
    if args.clear:
        logger.info("Clearing existing index...")
        embedder.clear_index()
        print("✓ Index cleared")

    # Run indexing
    print("Starting indexing...\n")
    try:
        stats = embedder.index_codebase(progress_callback=progress_callback)

        print("\n=== Indexing Complete ===")
        print(f"Files processed: {stats['files_processed']}")
        print(f"Chunks created: {stats['chunks_created']}")
        print(f"Errors: {stats['errors']}")

        if stats["errors"] > 0:
            logger.warning(f"{stats['errors']} files had errors during indexing")
            return 1

        return 0

    except KeyboardInterrupt:
        print("\n\nIndexing interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Indexing failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
