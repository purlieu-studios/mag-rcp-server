# Setting Up MAG MCP Server with Claude Desktop

This guide explains how to integrate the MAG MCP Server with Claude Desktop to give Claude access to your C# codebase through RAG-powered semantic search.

## Prerequisites

1. **Claude Desktop** installed ([Download here](https://claude.ai/download))
2. **MAG MCP Server** installed (run `.\install.ps1`)
3. **Ollama** running with required models:
   ```bash
   ollama pull nomic-embed-text
   ollama pull codestral
   ```

## Step 1: Index Your Codebase

Before using the MCP server, index your C# codebase:

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Index your codebase
mag-index --codebase "C:\path\to\your\csharp\project" -v

# Verify indexing
mag-index --stats
```

You should see output like:
```
=== Index Statistics ===
Total chunks: 150
Code types: class, method, interface, property
Collection: csharp_codebase
```

## Step 2: Locate Claude Desktop Configuration

The Claude Desktop configuration file is located at:

```
%APPDATA%\Claude\claude_desktop_config.json
```

Full path example:
```
C:\Users\YourUsername\AppData\Roaming\Claude\claude_desktop_config.json
```

**To quickly open it:**

**PowerShell:**
```powershell
notepad "$env:APPDATA\Claude\claude_desktop_config.json"
```

**Command Prompt:**
```cmd
notepad %APPDATA%\Claude\claude_desktop_config.json
```

## Step 3: Add MAG MCP Server to Configuration

Edit the `claude_desktop_config.json` file to add the MAG server.

### Example Configuration

```json
{
  "mcpServers": {
    "mag-csharp-rag": {
      "command": "C:\\programming\\rag-mcp-server\\venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "mag.server"
      ],
      "env": {
        "MAG_CODEBASE_ROOT": "C:\\path\\to\\your\\csharp\\project",
        "MAG_CHROMA_PERSIST_DIR": "C:\\Users\\YourUsername\\AppData\\Local\\mag\\chroma",
        "MAG_OLLAMA_HOST": "http://localhost:11434",
        "MAG_EMBEDDING_MODEL": "nomic-embed-text",
        "MAG_LLM_MODEL": "codestral"
      }
    }
  }
}
```

### If You Already Have Other MCP Servers

Add MAG as another entry:

```json
{
  "mcpServers": {
    "existing-server": {
      "command": "...",
      "args": ["..."]
    },
    "mag-csharp-rag": {
      "command": "C:\\programming\\rag-mcp-server\\venv\\Scripts\\python.exe",
      "args": ["-m", "mag.server"],
      "env": {
        "MAG_CODEBASE_ROOT": "C:\\path\\to\\your\\csharp\\project",
        "MAG_CHROMA_PERSIST_DIR": "C:\\Users\\YourUsername\\AppData\\Local\\mag\\chroma"
      }
    }
  }
}
```

### Important: Update These Paths

Replace the following with your actual paths:

1. **`command`**: Path to your venv Python executable
   - Find it: `Get-ChildItem .\venv\Scripts\python.exe | Select-Object FullName`

2. **`MAG_CODEBASE_ROOT`**: Your C# project directory
   - Example: `"C:\\Users\\YourName\\Projects\\MyGame"`

3. **`MAG_CHROMA_PERSIST_DIR`**: Where to store the vector database
   - Recommended: `"C:\\Users\\YourUsername\\AppData\\Local\\mag\\chroma"`

## Step 4: Restart Claude Desktop

1. **Quit Claude Desktop completely** (right-click system tray icon → Quit)
2. **Restart Claude Desktop**
3. Look for the MCP server icon in the chat interface

## Step 5: Verify Connection

In Claude Desktop, you should see:
- A small icon indicating MCP servers are connected
- When you click it, "mag-csharp-rag" should appear in the list

### Test the Connection

Ask Claude:
```
Can you search my codebase for entity management code?
```

Claude should now have access to these tools:

## Available Tools & Resources

### Tools (Functions Claude Can Call)

1. **`search_code`**
   - Semantically search your codebase
   - Example: "Find authentication logic"

2. **`get_file`**
   - Retrieve full file contents with optional AST
   - Example: "Show me EntityManager.cs"

3. **`list_files`**
   - List all indexed files with metadata
   - Can filter by pattern or type

4. **`explain_symbol`**
   - Get AI explanation of a specific symbol with context
   - Example: "Explain the CreateEntity method"

### Resources (Context Claude Can Access)

1. **`codebase://indexed`**
   - Summary of indexed codebase
   - Shows total chunks, file count, code types

2. **`codebase://stats`**
   - Real-time server statistics
   - Embedding model, LLM model, uptime, database size

### Prompts (Templates for Claude)

1. **`code_review`**
   - Template for reviewing code changes
   - Parameters: file_path, change_description

2. **`architecture_analysis`**
   - Template for analyzing system architecture
   - Parameters: namespace

## Example Conversations

### Example 1: Search and Explain
```
You: "Search for entity lifecycle management code and explain how it works"

Claude will:
1. Use search_code("entity lifecycle management")
2. Retrieve relevant code chunks
3. Use explain_symbol on key classes/methods
4. Provide a comprehensive explanation
```

### Example 2: Code Review
```
You: "Review the changes I made to PlayerController.cs where I added a new jump mechanic"

Claude will:
1. Use get_file("PlayerController.cs", include_ast=True)
2. Use the code_review prompt
3. Search for related physics/movement code
4. Provide architectural concerns, suggestions, testing recommendations
```

### Example 3: Architecture Analysis
```
You: "Analyze the GameEngine.Core namespace and create a diagram"

Claude will:
1. Use list_files with pattern matching
2. Retrieve files in that namespace
3. Use architecture_analysis prompt
4. Create Mermaid diagrams showing relationships
```

## Troubleshooting

### MCP Server Not Appearing

1. **Check configuration syntax**:
   ```powershell
   # Validate JSON
   Get-Content "$env:APPDATA\Claude\claude_desktop_config.json" | ConvertFrom-Json
   ```

2. **Verify paths**:
   ```powershell
   # Check Python exists
   Test-Path "C:\programming\rag-mcp-server\venv\Scripts\python.exe"

   # Test server manually
   & "C:\programming\rag-mcp-server\venv\Scripts\python.exe" -m mag.server
   ```

3. **Check Ollama is running**:
   ```bash
   # In terminal with venv activated
   mag-index --check-ollama
   ```

4. **View Claude Desktop logs**:
   - Logs location: `%APPDATA%\Claude\logs\`
   - Look for MCP server connection errors

### Server Starts But Tools Don't Work

1. **Verify indexing completed**:
   ```bash
   mag-index --stats
   ```
   Should show chunks > 0

2. **Check codebase path in config matches indexed path**

3. **Reindex if needed**:
   ```bash
   mag-index --clear
   mag-index -v
   ```

### "Ollama not available" Error

1. **Start Ollama**:
   ```bash
   ollama serve
   ```

2. **Pull required models**:
   ```bash
   ollama pull nomic-embed-text
   ollama pull codestral
   ```

3. **Verify connection**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

### Performance Issues

1. **Check database size**:
   ```bash
   mag-index --stats
   ```

2. **Optimize chunk size** (in config):
   ```json
   "env": {
     "MAG_CHUNK_SIZE_TOKENS": "256"
   }
   ```

3. **Increase max workers** (faster indexing):
   ```json
   "env": {
     "MAG_MAX_WORKERS": "8"
   }
   ```

## Updating the Codebase Index

As your code changes, reindex periodically:

```bash
# Quick reindex (updates changed files)
mag-index

# Full reindex (clears and rebuilds)
mag-index --clear

# Reindex specific paths
mag-index --codebase "C:\path\to\project"
```

**Note**: You don't need to restart Claude Desktop after reindexing. Changes take effect immediately.

## Advanced Configuration

### Custom Exclude Patterns

Add to environment variables in config:

```json
"env": {
  "MAG_EXCLUDE_PATTERNS": "[\"**/bin/**\", \"**/obj/**\", \"**/*.Designer.cs\"]"
}
```

### Multiple Codebases

Create separate MCP server entries:

```json
{
  "mcpServers": {
    "mag-game-engine": {
      "command": "C:\\...\\python.exe",
      "args": ["-m", "mag.server"],
      "env": {
        "MAG_CODEBASE_ROOT": "C:\\Projects\\GameEngine",
        "MAG_CHROMA_PERSIST_DIR": "C:\\...\\chroma_game"
      }
    },
    "mag-ui-framework": {
      "command": "C:\\...\\python.exe",
      "args": ["-m", "mag.server"],
      "env": {
        "MAG_CODEBASE_ROOT": "C:\\Projects\\UIFramework",
        "MAG_CHROMA_PERSIST_DIR": "C:\\...\\chroma_ui"
      }
    }
  }
}
```

### Using Different LLM Models

Change the models in the config:

```json
"env": {
  "MAG_EMBEDDING_MODEL": "nomic-embed-text",
  "MAG_LLM_MODEL": "llama3.1"
}
```

Make sure to pull the model first:
```bash
ollama pull llama3.1
```

## Best Practices

1. **Index before first use**: Always run `mag-index` before starting Claude Desktop

2. **Keep Ollama running**: Ensure Ollama is running whenever you use Claude with MAG

3. **Reindex after major changes**: After significant code changes, run `mag-index --clear`

4. **Use specific queries**: More specific searches yield better results
   - Good: "authentication middleware that validates JWT tokens"
   - Less good: "auth stuff"

5. **Monitor logs**: Check Claude Desktop logs if you encounter issues

## Getting Help

- **Installation issues**: See [INSTALLATION.md](INSTALLATION.md)
- **MCP Protocol**: [MCP Documentation](https://modelcontextprotocol.io)
- **Ollama setup**: [Ollama Documentation](https://ollama.ai)
- **Project issues**: Check the project README.md

## Configuration Helper Script

Use the included helper to generate your configuration:

```powershell
.\generate-claude-config.ps1 -CodebasePath "C:\path\to\project"
```

This will create a ready-to-use configuration file with the correct paths.
