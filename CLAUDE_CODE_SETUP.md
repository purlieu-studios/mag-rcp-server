# Setting Up MAG MCP Server with Claude Code

## Prerequisites

✅ Ollama installed and running (tested - working!)
✅ Python 3.14+ installed
✅ MAG package installed (`pip install -e .`)
✅ Codebase indexed (tested with `test_csharp_code`)

## Configuration Steps

### 1. Open Claude Code Settings

Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) and type "Settings" to open settings.

### 2. Add MCP Server Configuration

In your Claude Code settings, add the MCP server configuration:

```json
{
  "mcpServers": {
    "mag-csharp-rag": {
      "command": "python",
      "args": [
        "-m",
        "mag.server"
      ],
      "env": {
        "MAG_CODEBASE_ROOT": "C:\\programming\\rag-mcp-server\\test_csharp_code",
        "MAG_CHROMA_PERSIST_DIR": "C:\\programming\\rag-mcp-server\\data\\chroma",
        "MAG_OLLAMA_HOST": "http://localhost:11434",
        "MAG_EMBEDDING_MODEL": "nomic-embed-text",
        "MAG_LLM_MODEL": "codestral",
        "MAG_SIMILARITY_THRESHOLD": "0.5",
        "MAG_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Important**: Update the paths to match your system:
- `MAG_CODEBASE_ROOT`: Point to your C# codebase
- `MAG_CHROMA_PERSIST_DIR`: Where to store the vector database

### 3. Restart Claude Code

After adding the configuration, restart Claude Code to load the MCP server.

### 4. Verify MCP Server is Loaded

Look for the MCP server indicator in Claude Code. You should see "mag-csharp-rag" listed.

## Available MCP Tools

Once configured, Claude Code will have access to these tools:

### 1. `search_code` - Semantic code search
```
Search for code chunks by meaning, not just keywords
Parameters:
  - query: What you're looking for
  - max_results: Number of results (default: 5)
  - filter_type: Filter by type (class, method, interface, property, all)
```

### 2. `get_file` - Retrieve file contents
```
Get a file with optional AST parsing
Parameters:
  - file_path: Path relative to codebase root
  - include_ast: Include abstract syntax tree info (default: false)
```

### 3. `list_files` - List indexed files
```
List all files in the index with metadata
Parameters:
  - pattern: Glob pattern to filter files (optional)
  - filter_type: Filter by code type (optional)
```

### 4. `explain_symbol` - RAG-powered explanations
```
Get AI explanation of a symbol with codebase context
Parameters:
  - symbol_name: Name of the class/method/interface to explain
  - include_usage: Include usage examples (default: true)
```

## Example Queries in Claude Code

Once configured, you can ask Claude Code questions like:

- "Search for code related to user authentication"
- "Explain how the UserService class works"
- "Find all methods that handle email validation"
- "Show me the implementation of the authentication logic"

Claude Code will automatically use the MCP tools to search your indexed codebase!

## Testing the Configuration

### Test 1: Manual Tool Call

Ask Claude Code: "Use the search_code tool to find authentication-related code"

Expected: Should find `AuthenticateAsync` method in UserService.cs

### Test 2: Natural Question

Ask: "How does user authentication work in this codebase?"

Expected: Claude should use search_code to find relevant code and explain it

### Test 3: Symbol Explanation

Ask: "Explain the UserService class"

Expected: Claude should use explain_symbol to get a detailed explanation

## Troubleshooting

### MCP Server Not Loading

1. Check Claude Code logs for errors
2. Verify Python path is correct: `where python`
3. Test the server manually: `python -m mag.server`

### No Search Results

1. Check if codebase is indexed: `python -m mag.scripts.index_codebase --stats`
2. Lower similarity threshold in config (try 0.3-0.5)
3. Check Ollama is running: `python -m mag.scripts.index_codebase --check-ollama`

### Ollama Connection Errors

1. Start Ollama: `ollama serve`
2. Verify models are installed:
   - `ollama pull nomic-embed-text`
   - `ollama pull codestral`

## Performance Tips

- **Incremental Indexing**: Re-indexing is fast! Only changed files are processed
- **Similarity Threshold**: Lower values (0.3-0.5) return more results
- **Chunk Size**: Default 512 tokens works well for most code

## Next Steps

1. Index your actual C# codebase
2. Experiment with different search queries
3. Try the explain_symbol tool for complex classes
4. Use cross-project features (see MULTIPLE_PROJECTS.md)

---

**Status**: ✅ Tested and working with test_csharp_code
**Last Updated**: 2025-10-31
