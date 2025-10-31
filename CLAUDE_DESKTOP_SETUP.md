# Setting Up MAG MCP Server with Claude Desktop

## What is This?

MAG is an **MCP (Model Context Protocol) server** that gives Claude semantic search capabilities over your C# codebase. Once configured, you can ask Claude questions about your code and it will automatically search and analyze your codebase to answer.

## Prerequisites

Before setting up, ensure you have:

- ✅ **Claude Desktop** installed ([download here](https://claude.ai/download))
- ✅ **Ollama** installed and running ([download here](https://ollama.ai))
- ✅ **Python 3.10+** installed
- ✅ **This package installed**: `pip install -e .` (from this repo)

## Step 1: Install Required Ollama Models

Open a terminal and run:

```bash
# For embeddings (required)
ollama pull nomic-embed-text

# For explanations (optional but recommended)
ollama pull codestral
```

Wait for the models to download (this may take a few minutes).

## Step 2: Index Your C# Codebase

Index your codebase once before using Claude Desktop:

```bash
# Navigate to this repo
cd C:\programming\rag-mcp-server

# Index your C# codebase (replace path with your actual codebase)
python -m mag.scripts.index_codebase --codebase "C:\path\to\your\csharp\project"

# Or test with the sample code first:
python -m mag.scripts.index_codebase --codebase test_csharp_code
```

You should see output like:
```
=== Indexing Complete ===
Files processed: 2
Chunks created: 14
Errors: 0
```

## Step 3: Configure Claude Desktop

### Option A: Windows

1. **Locate your Claude Desktop config file**:
   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```
   Full path is typically:
   ```
   C:\Users\YourUsername\AppData\Roaming\Claude\claude_desktop_config.json
   ```

2. **Edit the config file** (create it if it doesn't exist):

   Open in your favorite text editor and add:

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
           "MAG_CODEBASE_ROOT": "C:\\path\\to\\your\\csharp\\project",
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

   **Important**: Replace these paths:
   - `MAG_CODEBASE_ROOT`: Path to YOUR C# codebase
   - `MAG_CHROMA_PERSIST_DIR`: Where the index is stored (can keep this)

### Option B: macOS/Linux

1. **Locate your Claude Desktop config file**:
   ```bash
   # macOS
   ~/Library/Application Support/Claude/claude_desktop_config.json

   # Linux
   ~/.config/Claude/claude_desktop_config.json
   ```

2. **Edit the config file**:

   ```json
   {
     "mcpServers": {
       "mag-csharp-rag": {
         "command": "python3",
         "args": [
           "-m",
           "mag.server"
         ],
         "env": {
           "MAG_CODEBASE_ROOT": "/path/to/your/csharp/project",
           "MAG_CHROMA_PERSIST_DIR": "/path/to/rag-mcp-server/data/chroma",
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

   **Note**: Use forward slashes `/` on macOS/Linux

## Step 4: Restart Claude Desktop

1. **Quit Claude Desktop completely** (don't just close the window)
   - Windows: Right-click system tray icon → Quit
   - macOS: Claude → Quit Claude

2. **Restart Claude Desktop**

3. **Verify MCP server loaded**:
   - Look for a small hammer/wrench icon (🔨) in the bottom right
   - Click it to see available MCP servers
   - You should see "mag-csharp-rag" listed

## Step 5: Test It Out!

Start a new conversation in Claude Desktop and try these queries:

### Test 1: Search for code
```
Search my codebase for authentication-related code
```

Claude should use the `search_code` tool and show you relevant code snippets.

### Test 2: Explain a concept
```
Explain how user authentication works in my codebase
```

Claude should search for auth-related code and explain it with context.

### Test 3: Find specific patterns
```
Find all methods that validate email addresses
```

### Test 4: List files
```
What files are indexed in my codebase?
```

## Configuration Options

You can customize the behavior by changing environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MAG_CODEBASE_ROOT` | Path to your C# codebase | Required |
| `MAG_CHROMA_PERSIST_DIR` | Where to store the vector database | `./data/chroma` |
| `MAG_OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `MAG_EMBEDDING_MODEL` | Model for embeddings | `nomic-embed-text` |
| `MAG_LLM_MODEL` | Model for explanations | `codestral` |
| `MAG_SIMILARITY_THRESHOLD` | Search relevance threshold (0-1) | `0.7` |
| `MAG_DEFAULT_SEARCH_RESULTS` | Number of results to return | `5` |
| `MAG_CHUNK_SIZE_TOKENS` | Chunk size for indexing | `512` |
| `MAG_LOG_LEVEL` | Logging level | `INFO` |

**Tip**: Lower `MAG_SIMILARITY_THRESHOLD` (e.g., `0.3-0.5`) to get more search results.

## Available MCP Tools

Once configured, Claude Desktop will have access to these tools:

### 🔍 `search_code`
Search for code chunks by semantic meaning (not just keywords)

**Example**: "Search for code that handles file uploads"

### 📄 `get_file`
Retrieve a specific file with optional AST parsing

**Example**: "Show me the UserService.cs file with its structure"

### 📋 `list_files`
List all indexed files with metadata and filters

**Example**: "List all interface files in the codebase"

### 💡 `explain_symbol`
Get AI-powered explanations of classes/methods with codebase context

**Example**: "Explain the UserRepository class"

## Troubleshooting

### MCP Server Not Showing Up

**Check 1**: Verify config file location
```bash
# Windows
type %APPDATA%\Claude\claude_desktop_config.json

# macOS/Linux
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Check 2**: Validate JSON syntax
- Use [JSONLint](https://jsonlint.com/) to check for errors
- Common issue: Missing commas or quotes

**Check 3**: Test the server manually
```bash
python -m mag.server
```
Should start without errors (Ctrl+C to stop)

### Search Returns No Results

**Fix 1**: Lower similarity threshold in config
```json
"MAG_SIMILARITY_THRESHOLD": "0.3"
```

**Fix 2**: Verify codebase is indexed
```bash
python -m mag.scripts.index_codebase --stats
```
Should show files and chunks.

**Fix 3**: Check if Ollama is running
```bash
python -m mag.scripts.index_codebase --check-ollama
```

### Ollama Connection Errors

**Fix 1**: Start Ollama
```bash
# It should start automatically, but if not:
ollama serve
```

**Fix 2**: Verify models are installed
```bash
ollama list
```
Should show `nomic-embed-text` and `codestral`

### Performance Issues

**Symptom**: Slow search responses

**Fix 1**: Use faster embedding model
```json
"MAG_EMBEDDING_MODEL": "all-minilm"
```

**Fix 2**: Reduce chunk size
```json
"MAG_CHUNK_SIZE_TOKENS": "256"
```

**Fix 3**: Enable incremental indexing (automatic by default)
```bash
# Re-index (only processes changed files - much faster!)
python -m mag.scripts.index_codebase --codebase path/to/code
```

## Updating the Index

### When to Re-Index

Re-index your codebase when:
- You add new C# files
- You modify existing code
- You want the latest changes searchable

### How to Re-Index

**Incremental (Fast - Recommended)**:
```bash
python -m mag.scripts.index_codebase --codebase path/to/code
```
Only processes changed files!

**Full Re-Index**:
```bash
python -m mag.scripts.index_codebase --codebase path/to/code --clear
```
Processes all files from scratch.

## Multiple Codebases

You can configure multiple MCP servers for different projects:

```json
{
  "mcpServers": {
    "mag-project-a": {
      "command": "python",
      "args": ["-m", "mag.server"],
      "env": {
        "MAG_CODEBASE_ROOT": "C:\\projects\\project-a",
        "MAG_CHROMA_PERSIST_DIR": "C:\\rag-mcp-server\\data\\project-a",
        "MAG_CHROMA_COLLECTION_NAME": "project_a_code"
      }
    },
    "mag-project-b": {
      "command": "python",
      "args": ["-m", "mag.server"],
      "env": {
        "MAG_CODEBASE_ROOT": "C:\\projects\\project-b",
        "MAG_CHROMA_PERSIST_DIR": "C:\\rag-mcp-server\\data\\project-b",
        "MAG_CHROMA_COLLECTION_NAME": "project_b_code"
      }
    }
  }
}
```

Each project gets its own isolated index!

## Example Conversation

Here's what a conversation with Claude Desktop looks like once MAG is configured:

**You**: "Find all the authentication methods in my codebase"

**Claude**:
> I'll search for authentication-related code.
>
> *[Uses search_code tool]*
>
> I found several authentication methods:
>
> 1. **AuthenticateAsync** in `UserService.cs`
>    - Handles user login with email/password
>    - Returns JWT token on success
>    - Checks if account is active
>
> 2. **VerifyPassword** in `User.cs`
>    - Validates password hash
>    - Uses BCrypt for security
>
> Would you like me to explain how any of these work in detail?

**You**: "Explain the AuthenticateAsync method"

**Claude**:
> *[Uses explain_symbol tool]*
>
> The `AuthenticateAsync` method in `UserService.cs` handles user authentication:
>
> ```csharp
> public async Task<AuthResult> AuthenticateAsync(string email, string password)
> {
>     // Gets user from database
>     var user = await _userRepository.GetByEmailAsync(email);
>
>     // Validates credentials
>     if (user == null || !user.VerifyPassword(password))
>         return AuthResult.Failed("Invalid credentials");
>
>     // Checks account status
>     if (!user.IsActive)
>         return AuthResult.Failed("Account is inactive");
>
>     // Generates JWT token
>     var token = GenerateJwtToken(user);
>     return AuthResult.Success(token, user);
> }
> ```
>
> This follows a standard authentication flow with proper error handling.

## Security Notes

⚠️ **Important**: This MCP server runs locally on your machine and:
- Only accesses files you explicitly configure
- Sends code snippets to your local Ollama instance (not external servers)
- Stores embeddings locally in the vector database
- Does not transmit your code to Claude's servers

Your code stays on your machine! 🔒

## Need Help?

- 📖 **Full Documentation**: See README.md in this repo
- 🐛 **Report Issues**: https://github.com/purlieu-studios/mag-rcp-server/issues
- 💬 **Questions**: Check existing issues or open a new one

---

**Last Updated**: 2025-10-31
**Version**: 0.1.0
**Status**: ✅ Tested and working
