# MAG MCP Server

**Model Context Protocol (MCP) server for indexing and querying C# codebases using Ollama embeddings and RAG.**

MAG provides semantic code search, file retrieval, and AI-powered code explanations for C# projects through the standardized MCP interface. It enables LLMs like Claude to understand and reason about your codebase.

## Features

- **Semantic Code Search**: Find code by meaning, not just keywords
- **Smart Chunking**: Automatically breaks code into semantically meaningful chunks
- **RAG-Powered Explanations**: Get AI explanations with codebase context
- **File Operations**: Retrieve files with optional AST parsing
- **MCP Resources**: Access codebase statistics and index information
- **Prompt Templates**: Built-in templates for code review and architecture analysis

## Architecture

```
Claude Desktop/AI → MCP Protocol → MAG Server → Ollama (embeddings)
                                              → ChromaDB (vector storage)
                                              → C# Codebase (tree-sitter parsing)
```

## Prerequisites

- **Python 3.14** (as specified in your requirements)
- **Ollama** running locally with models:
  - `nomic-embed-text` (for embeddings)
  - `codestral` or `deepseek-coder` (for explanations)

## Installation

### 1. Install Ollama

```bash
# Visit https://ollama.ai/download and install Ollama
# Then pull required models:
ollama pull nomic-embed-text
ollama pull codestral
```

### 2. Install MAG

```bash
# Clone the repository
git clone <your-repo-url>
cd rag-mcp-server

# Install dependencies
pip install -e .

# For development with testing tools
pip install -e ".[dev]"
```

### 3. Configure Environment

Copy the example environment file and customize:

```bash
cp .env.example .env
```

Edit `.env` to set your codebase path:

```env
MAG_CODEBASE_ROOT=/path/to/your/csharp/project
MAG_OLLAMA_HOST=http://localhost:11434
```

## Usage

### Index Your Codebase

Before using MAG with Claude, you need to index your C# codebase:

```bash
# Check Ollama connection
mag-index --check-ollama

# Index your codebase
mag-index --codebase /path/to/your/csharp/project

# Clear and reindex
mag-index --clear --codebase /path/to/your/project

# Show index statistics
mag-index --stats
```

### Configure Claude Desktop

Add MAG to your Claude Desktop MCP configuration. On Windows, edit:

```
%APPDATA%\Claude\claude_desktop_config.json
```

Add the MAG server:

```json
{
  "mcpServers": {
    "mag-csharp": {
      "command": "python",
      "args": ["-m", "mag.server"],
      "env": {
        "MAG_CODEBASE_ROOT": "C:\\path\\to\\your\\csharp\\project",
        "MAG_OLLAMA_HOST": "http://localhost:11434"
      }
    }
  }
}
```

Restart Claude Desktop. MAG tools should now appear in the MCP tools list.

### Using MAG Tools in Claude

Once configured, you can ask Claude to use MAG tools:

**Search for code:**
```
Can you search for classes related to entity management in the codebase?
```

**Get file contents:**
```
Show me the contents of Core/EntityManager.cs
```

**List indexed files:**
```
List all the interface files in the codebase
```

**Explain symbols:**
```
Explain how the CreateEntity method works
```

## MCP Tools

### `search_code`

Search for code chunks semantically similar to a query.

**Parameters:**
- `query` (string, required): Search query
- `max_results` (integer, optional): Maximum results (default: 5)
- `filter_type` (enum, optional): Filter by type: `class`, `method`, `interface`, `property`, `all`

**Example:**
```json
{
  "query": "entity creation and lifecycle management",
  "max_results": 10,
  "filter_type": "class"
}
```

### `get_file`

Retrieve full file contents with optional AST.

**Parameters:**
- `path` (string, required): Relative path from codebase root
- `include_ast` (boolean, optional): Include AST information (default: false)

**Example:**
```json
{
  "path": "Core/EntityManager.cs",
  "include_ast": true
}
```

### `list_files`

List all indexed files with metadata.

**Parameters:**
- `pattern` (string, optional): Glob pattern (e.g., `**/*Manager.cs`)
- `type_filter` (enum, optional): Filter by type: `class`, `interface`, `struct`, `all`

**Example:**
```json
{
  "pattern": "**/I*.cs",
  "type_filter": "interface"
}
```

### `explain_symbol`

Get AI-powered explanation of a symbol with codebase context.

**Parameters:**
- `symbol` (string, required): Symbol name (e.g., `EntityManager.CreateEntity`)
- `include_usage` (boolean, optional): Include usage examples (default: true)

**Example:**
```json
{
  "symbol": "EntityManager.CreateEntity",
  "include_usage": true
}
```

## MCP Resources

### `codebase://indexed`

JSON summary of the indexed codebase including file count, chunk statistics, and code types.

### `codebase://stats`

Real-time server statistics including:
- Vector database size
- Embedding and LLM models in use
- Server uptime
- Configuration settings

## MCP Prompts

### `code_review`

Template for reviewing code changes with codebase context.

**Arguments:**
- `file_path`: Path to file being reviewed
- `change_description`: Description of changes

### `architecture_analysis`

Template for analyzing system architecture.

**Arguments:**
- `namespace`: Namespace to analyze

## Configuration

All configuration is done via environment variables with the `MAG_` prefix:

| Variable | Description | Default |
|----------|-------------|---------|
| `MAG_CODEBASE_ROOT` | Path to C# codebase | Current directory |
| `MAG_OLLAMA_HOST` | Ollama API host | `http://localhost:11434` |
| `MAG_EMBEDDING_MODEL` | Ollama embedding model | `nomic-embed-text` |
| `MAG_LLM_MODEL` | Ollama LLM model | `codestral` |
| `MAG_CHROMA_PERSIST_DIR` | ChromaDB storage path | `./data/chroma` |
| `MAG_CHUNK_SIZE_TOKENS` | Target chunk size | `512` |
| `MAG_SIMILARITY_THRESHOLD` | Minimum similarity | `0.7` |

See `.env.example` for all available options.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mag --cov-report=html

# Run specific test file
pytest tests/test_parser.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Lint code
ruff check src/ tests/

# Format code
ruff format src/ tests/

# Type checking
mypy src/
```

### Project Structure

```
mag-mcp-server/
├── src/mag/
│   ├── server.py              # MCP server entry point
│   ├── config.py              # Configuration management
│   ├── tools/                 # MCP tool implementations
│   │   ├── search_code.py
│   │   ├── get_file.py
│   │   ├── list_files.py
│   │   └── explain_symbol.py
│   ├── resources/             # MCP resources
│   │   ├── codebase_indexed.py
│   │   └── stats.py
│   ├── prompts/               # MCP prompts
│   │   ├── code_review.py
│   │   └── architecture.py
│   ├── indexer/               # Indexing pipeline
│   │   ├── discovery.py       # File discovery
│   │   ├── parser.py          # C# parsing (tree-sitter)
│   │   ├── chunker.py         # Semantic chunking
│   │   └── embedder.py        # Indexing orchestration
│   ├── retrieval/             # Vector search
│   │   └── vector_store.py    # ChromaDB wrapper
│   ├── llm/                   # LLM integration
│   │   └── ollama_client.py   # Ollama API client
│   └── scripts/               # CLI tools
│       └── index_codebase.py  # Indexing CLI
├── tests/                     # Comprehensive test suite
├── pyproject.toml             # Project configuration
└── mcp.json                   # MCP configuration example
```

## Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Verify models are available
ollama list

# Test embedding generation
mag-index --check-ollama
```

### Index Not Updating

```bash
# Clear and rebuild index
mag-index --clear --codebase /path/to/project

# Check index statistics
mag-index --stats
```

### Claude Desktop Not Showing Tools

1. Verify `claude_desktop_config.json` is correct
2. Restart Claude Desktop completely
3. Check logs in Claude Desktop (Help → View Logs)
4. Ensure Python and dependencies are installed

### Poor Search Results

- Increase `MAG_DEFAULT_SEARCH_RESULTS`
- Lower `MAG_SIMILARITY_THRESHOLD`
- Try more specific queries
- Reindex after code changes

## License

MIT

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
