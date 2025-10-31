# Setting Up MAG MCP Server with Claude

MAG is an **MCP (Model Context Protocol) server** that gives Claude semantic search capabilities over your C# codebase. Once configured, you can ask Claude questions about your code and it will automatically search and analyze your codebase.

## Quick Start

```bash
# 1. Install dependencies
pip install -e .
ollama pull nomic-embed-text

# 2. Index your C# codebase
python -m mag.scripts.index_codebase --codebase /path/to/your/csharp/project

# 3. Configure Claude (see below for Desktop vs Code)

# 4. Ask Claude: "Search my codebase for authentication code"
```

## Prerequisites

- ✅ **Claude Desktop** or **Claude Code** ([download](https://claude.ai/download))
- ✅ **Ollama** installed and running ([download](https://ollama.ai))
- ✅ **Python 3.10+** installed
- ✅ **MAG installed**: `pip install -e .` (from this repo)

## Installation

### 1. Install Ollama Models

```bash
# For embeddings (required)
ollama pull nomic-embed-text

# For explanations (optional but recommended)
ollama pull codestral
```

### 2. Index Your Codebase

```bash
# Index your C# project
python -m mag.scripts.index_codebase --codebase "C:\path\to\your\csharp\project"

# Or test with sample code
python -m mag.scripts.index_codebase --codebase test_csharp_code
```

Expected output:
```
=== Indexing Complete ===
Files processed: 2
Chunks created: 14
Errors: 0
```

## Configuration

Choose your Claude interface:

---

## A. Claude Desktop Setup

### 1. Locate Config File

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### 2. Add MCP Server Configuration

Edit (or create) `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mag-csharp-rag": {
      "command": "python",
      "args": ["-m", "mag.server"],
      "env": {
        "MAG_CODEBASE_ROOT": "C:\\path\\to\\your\\csharp\\project",
        "MAG_CHROMA_PERSIST_DIR": "C:\\programming\\rag-mcp-server\\data\\chroma",
        "MAG_OLLAMA_HOST": "http://localhost:11434",
        "MAG_SIMILARITY_THRESHOLD": "0.5"
      }
    }
  }
}
```

**Important:**
- Use `python3` instead of `python` on macOS/Linux
- Use forward slashes `/` on macOS/Linux
- Replace `MAG_CODEBASE_ROOT` with your actual codebase path

### 3. Restart Claude Desktop

Quit completely and relaunch. Look for the hammer icon (🔨) to verify the MCP server loaded.

---

## B. Claude Code Setup

### 1. Open Claude Code Settings

In VS Code:
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type "Settings"
3. Search for "MCP"
4. Click "Edit in settings.json"

### 2. Add MCP Configuration

```json
{
  "mcpServers": {
    "mag-csharp-rag": {
      "command": "python",
      "args": ["-m", "mag.server"],
      "env": {
        "MAG_CODEBASE_ROOT": "C:\\path\\to\\your\\csharp\\project",
        "MAG_CHROMA_PERSIST_DIR": "C:\\programming\\rag-mcp-server\\data\\chroma",
        "MAG_OLLAMA_HOST": "http://localhost:11434",
        "MAG_SIMILARITY_THRESHOLD": "0.5"
      }
    }
  }
}
```

### 3. Reload VS Code

Press `Ctrl+Shift+P` → "Reload Window"

---

## Using MAG with Claude

Once configured, Claude has access to these tools:

### 🔍 `search_code`
Search for code by semantic meaning

**Example:** "Search for authentication-related code"

### 📄 `get_file`
Retrieve a file with optional AST parsing

**Example:** "Show me UserService.cs"

### 📋 `list_files`
List all indexed files with filters

**Example:** "List all interface files"

### 💡 `explain_symbol`
Get AI explanations with codebase context

**Example:** "Explain the UserRepository class"

## Example Conversation

**You:** Find all authentication methods in my codebase

**Claude:**
> I'll search for authentication-related code.
>
> *[Uses search_code tool]*
>
> I found:
> 1. **AuthenticateAsync** in UserService.cs
>    - Handles login with email/password
>    - Returns JWT token
>
> Would you like me to explain how it works?

**You:** Explain the AuthenticateAsync method

**Claude:**
> *[Uses explain_symbol tool]*
>
> The `AuthenticateAsync` method:
> - Retrieves user by email
> - Verifies password
> - Checks if account is active
> - Generates JWT token
>
> [Shows code and explanation]

## Configuration Options

Customize behavior via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MAG_CODEBASE_ROOT` | Path to C# codebase | **Required** |
| `MAG_CHROMA_PERSIST_DIR` | Vector database location | `./data/chroma` |
| `MAG_OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `MAG_SIMILARITY_THRESHOLD` | Search relevance (0-1) | `0.7` |
| `MAG_EMBEDDING_MODEL` | Embedding model | `nomic-embed-text` |
| `MAG_LLM_MODEL` | Explanation model | `codestral` |
| `MAG_CHUNK_SIZE_TOKENS` | Chunk size | `512` |
| `MAG_LOG_LEVEL` | Logging level | `INFO` |

**Tip:** Lower `MAG_SIMILARITY_THRESHOLD` (e.g., 0.3-0.5) for more results.

## Multiple Codebases

Configure multiple projects:

```json
{
  "mcpServers": {
    "mag-project-a": {
      "command": "python",
      "args": ["-m", "mag.server"],
      "env": {
        "MAG_CODEBASE_ROOT": "/path/to/project-a",
        "MAG_CHROMA_PERSIST_DIR": "/data/project-a",
        "MAG_CHROMA_COLLECTION_NAME": "project_a"
      }
    },
    "mag-project-b": {
      "command": "python",
      "args": ["-m", "mag.server"],
      "env": {
        "MAG_CODEBASE_ROOT": "/path/to/project-b",
        "MAG_CHROMA_PERSIST_DIR": "/data/project-b",
        "MAG_CHROMA_COLLECTION_NAME": "project_b"
      }
    }
  }
}
```

See [MULTIPLE_PROJECTS.md](MULTIPLE_PROJECTS.md) for details.

## Re-indexing Your Codebase

### Incremental (Fast - Recommended)
Only processes changed files:
```bash
python -m mag.scripts.index_codebase --codebase /path/to/code
```

### Full Re-index
Processes everything:
```bash
python -m mag.scripts.index_codebase --codebase /path/to/code --clear
```

### Check Status
```bash
python -m mag.scripts.index_codebase --stats
```

## Troubleshooting

### MCP Server Not Loading

**Check config file exists:**
```bash
# Windows
type %APPDATA%\Claude\claude_desktop_config.json

# macOS/Linux
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Validate JSON syntax:** Use [JSONLint](https://jsonlint.com/)

**Test server manually:**
```bash
python -m mag.server
# Should start without errors (Ctrl+C to stop)
```

### No Search Results

**Lower similarity threshold:**
```json
"MAG_SIMILARITY_THRESHOLD": "0.3"
```

**Verify indexing:**
```bash
python -m mag.scripts.index_codebase --stats
```

**Check Ollama:**
```bash
python -m mag.scripts.index_codebase --check-ollama
```

### Ollama Connection Errors

**Verify Ollama is running:**
```bash
ollama list
```

**Check models installed:**
Should show `nomic-embed-text` and `codestral`

**Restart Ollama:**
```bash
ollama serve
```

### Slow Performance

**Use faster model:**
```json
"MAG_EMBEDDING_MODEL": "all-minilm"
```

**Reduce chunk size:**
```json
"MAG_CHUNK_SIZE_TOKENS": "256"
```

**Enable incremental indexing** (enabled by default)

## Security

⚠️ **Important:** MAG runs locally and:
- Only accesses files you configure
- Sends code to your local Ollama (not external servers)
- Stores embeddings locally
- Does not transmit code to Claude's servers

Your code stays on your machine! 🔒

## Advanced Topics

- **Multi-project setup:** See [MULTIPLE_PROJECTS.md](MULTIPLE_PROJECTS.md)
- **Custom chunking:** Adjust `MAG_CHUNK_SIZE_TOKENS`
- **Filter by type:** Use `filter_type` parameter in searches
- **Namespace filtering:** Coming soon

## Need Help?

- 📖 **Project README:** [README.md](README.md)
- 🐛 **Report Issues:** [GitHub Issues](https://github.com/purlieu-studios/mag-rcp-server/issues)
- 💬 **Discussions:** Check existing issues or open a new one

---

**Last Updated:** 2025-10-31
**Version:** 0.1.0
**Status:** ✅ Tested and working
