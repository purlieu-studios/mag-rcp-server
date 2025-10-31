# Quick Start: Using MAG with Claude Desktop

Get your C# codebase connected to Claude in 5 minutes!

## Prerequisites

- ✅ Claude Desktop installed
- ✅ Ollama running with models: `ollama pull nomic-embed-text` & `ollama pull codestral`

## Step 1: Install MAG (1 minute)

```powershell
# Run the installation script
.\install.ps1

# Activate environment
.\venv\Scripts\Activate.ps1
```

## Step 2: Index Your Codebase (2-5 minutes)

```bash
# Index your C# project
mag-index --codebase "C:\path\to\your\csharp\project" -v

# Verify it worked
mag-index --stats
```

You should see:
```
Total chunks: 150+
Code types: class, method, interface, property
```

## Step 3: Generate Claude Config (30 seconds)

```powershell
# Generate configuration automatically
.\generate-claude-config.ps1 -CodebasePath "C:\path\to\your\project" -OpenConfig
```

This will:
1. Create the configuration
2. Open Claude Desktop's config file
3. Show you exactly what to paste

**OR manually create/edit:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

Add this configuration:
```json
{
  "mcpServers": {
    "mag-csharp-rag": {
      "command": "C:\\programming\\rag-mcp-server\\venv\\Scripts\\python.exe",
      "args": ["-m", "mag.server"],
      "env": {
        "MAG_CODEBASE_ROOT": "C:\\path\\to\\your\\project",
        "MAG_CHROMA_PERSIST_DIR": "C:\\Users\\YourName\\AppData\\Local\\mag\\chroma"
      }
    }
  }
}
```

## Step 4: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Start it again
3. Look for the MCP server indicator (icon in chat)

## Step 5: Test It!

In Claude Desktop, try:

```
Search my codebase for entity management code
```

or

```
List all the files you have indexed
```

or

```
Explain how the PlayerController class works
```

## What Claude Can Now Do

### 🔍 Search Your Code
```
"Find all classes that implement IRepository"
"Search for authentication logic"
"Show me entity lifecycle management code"
```

### 📄 Get Files
```
"Show me the EntityManager.cs file"
"Get the Player.cs file with AST structure"
```

### 📋 List Files
```
"List all files in the GameEngine namespace"
"Show me all interface files"
```

### 💡 Explain Code
```
"Explain the CreateEntity method"
"How does the combat system work?"
"What does the PhysicsComponent do?"
```

### 🏗️ Architecture Analysis
```
"Analyze the GameEngine.Core namespace"
"Show me the architecture of the UI system"
"Create a diagram of component relationships"
```

### 🔎 Code Review
```
"Review my changes to PlayerController.cs where I added double jump"
```

## Troubleshooting

### Server Not Showing Up?

```powershell
# 1. Validate your config
Get-Content "$env:APPDATA\Claude\claude_desktop_config.json" | ConvertFrom-Json

# 2. Test server manually
.\venv\Scripts\Activate.ps1
python -m mag.server

# 3. Check Ollama
mag-index --check-ollama
```

### No Results When Searching?

```bash
# Reindex your codebase
mag-index --clear
mag-index -v
```

### Tools Not Working?

1. Make sure `MAG_CODEBASE_ROOT` in config matches the path you indexed
2. Verify indexing completed: `mag-index --stats`
3. Check Claude Desktop logs: `%APPDATA%\Claude\logs\`

## Pro Tips

1. **Be specific in searches**: "JWT authentication middleware" > "auth stuff"

2. **Use explain_symbol for deep dives**: "Explain the EntityManager class with usage examples"

3. **Reindex after big changes**: `mag-index --clear` when you refactor

4. **Check stats regularly**: `mag-index --stats` to see what's indexed

5. **Multiple projects**: Create separate config entries for each codebase

## Example Conversations

### Find & Explain
```
You: "Search for player movement code and explain how it handles physics"

Claude uses:
1. search_code("player movement physics")
2. get_file("PlayerController.cs", include_ast=True)
3. explain_symbol("PlayerController.Move")
4. Provides comprehensive explanation with code references
```

### Architecture Review
```
You: "I want to understand the entity component system architecture"

Claude uses:
1. list_files(pattern="**/Components/**")
2. search_code("entity component system")
3. architecture_analysis_prompt(namespace="GameEngine.ECS")
4. Creates Mermaid diagram + explanation
```

### Code Review
```
You: "Review my PlayerHealth.cs changes where I added regeneration"

Claude uses:
1. get_file("PlayerHealth.cs", include_ast=True)
2. search_code("health regeneration patterns")
3. code_review_prompt with your changes
4. Provides feedback on architecture, testing, performance
```

## What's Next?

- **Full documentation**: See [CLAUDE_SETUP.md](CLAUDE_SETUP.md)
- **Installation help**: See [INSTALLATION.md](INSTALLATION.md)
- **Configuration options**: See example in [claude_desktop_config.json](claude_desktop_config.json)

## Need Help?

1. Check [CLAUDE_SETUP.md](CLAUDE_SETUP.md) for detailed troubleshooting
2. Verify Ollama: `ollama list` should show your models
3. Test indexing: `mag-index --stats` should show chunks > 0
4. Check Claude logs: `%APPDATA%\Claude\logs\mcp*.log`

---

**Ready?** Run these 3 commands:

```powershell
.\install.ps1
mag-index --codebase "C:\your\project"
.\generate-claude-config.ps1 -OpenConfig
```

Then restart Claude Desktop and start asking about your code! 🚀
