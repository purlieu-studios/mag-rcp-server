# Managing Multiple C# Projects with MAG MCP Server

This guide shows how to index and use multiple C# codebases simultaneously with Claude Desktop.

## How It Works

Each project gets:
- ✅ Its own vector database (separate Qdrant collection)
- ✅ Its own MCP server instance in Claude Desktop
- ✅ Independent indexing and querying
- ✅ No conflicts or mixed results

## Quick Setup

### 1. Index Each Project Separately

```powershell
# Project A
$env:MAG_CODEBASE_ROOT = "C:\Projects\GameEngine"
$env:MAG_CHROMA_PERSIST_DIR = "C:\Users\YourName\AppData\Local\mag\chroma_game"
mag-index -v

# Project B
$env:MAG_CODEBASE_ROOT = "C:\Projects\UIFramework"
$env:MAG_CHROMA_PERSIST_DIR = "C:\Users\YourName\AppData\Local\mag\chroma_ui"
mag-index -v

# Project C
$env:MAG_CODEBASE_ROOT = "C:\Projects\NetworkingLib"
$env:MAG_CHROMA_PERSIST_DIR = "C:\Users\YourName\AppData\Local\mag\chroma_net"
mag-index -v
```

**Important**: Each project MUST have a different `MAG_CHROMA_PERSIST_DIR`!

### 2. Configure Claude Desktop for Multiple Projects

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mag-game-engine": {
      "command": "C:\\programming\\rag-mcp-server\\venv\\Scripts\\python.exe",
      "args": ["-m", "mag.server"],
      "env": {
        "MAG_CODEBASE_ROOT": "C:\\Projects\\GameEngine",
        "MAG_CHROMA_PERSIST_DIR": "C:\\Users\\YourName\\AppData\\Local\\mag\\chroma_game",
        "MAG_CHROMA_COLLECTION_NAME": "game_engine",
        "MAG_OLLAMA_HOST": "http://localhost:11434"
      }
    },
    "mag-ui-framework": {
      "command": "C:\\programming\\rag-mcp-server\\venv\\Scripts\\python.exe",
      "args": ["-m", "mag.server"],
      "env": {
        "MAG_CODEBASE_ROOT": "C:\\Projects\\UIFramework",
        "MAG_CHROMA_PERSIST_DIR": "C:\\Users\\YourName\\AppData\\Local\\mag\\chroma_ui",
        "MAG_CHROMA_COLLECTION_NAME": "ui_framework",
        "MAG_OLLAMA_HOST": "http://localhost:11434"
      }
    },
    "mag-networking": {
      "command": "C:\\programming\\rag-mcp-server\\venv\\Scripts\\python.exe",
      "args": ["-m", "mag.server"],
      "env": {
        "MAG_CODEBASE_ROOT": "C:\\Projects\\NetworkingLib",
        "MAG_CHROMA_PERSIST_DIR": "C:\\Users\\YourName\\AppData\\Local\\mag\\chroma_net",
        "MAG_CHROMA_COLLECTION_NAME": "networking_lib",
        "MAG_OLLAMA_HOST": "http://localhost:11434"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

After restarting, you'll see all three MCP servers in Claude!

## Using Multiple Projects

### Claude Can Access All Projects Simultaneously

When you ask Claude:
```
"Search my game engine for entity management code"
```

Claude will know to use the `mag-game-engine` server.

Or:
```
"Find button components in my UI framework"
```

Claude uses the `mag-ui-framework` server.

### Cross-Project Queries

You can even ask Claude to compare across projects:
```
"Compare the networking implementation in my game engine
vs the networking library"
```

Claude will query both servers and synthesize the results!

## Helper Script: Generate Multi-Project Config

Use the included script to easily add projects:

```powershell
# Generate config for your first project
.\generate-multi-project-config.ps1 `
    -ProjectName "GameEngine" `
    -CodebasePath "C:\Projects\GameEngine" `
    -OutputFile "claude_config_multi.json"

# Add another project to the same config
.\generate-multi-project-config.ps1 `
    -ProjectName "UIFramework" `
    -CodebasePath "C:\Projects\UIFramework" `
    -AppendTo "claude_config_multi.json"

# Add a third project
.\generate-multi-project-config.ps1 `
    -ProjectName "Networking" `
    -CodebasePath "C:\Projects\NetworkingLib" `
    -AppendTo "claude_config_multi.json"
```

Then copy the contents to your Claude Desktop config.

## Reindexing Individual Projects

Each project can be reindexed independently:

```powershell
# Reindex GameEngine (doesn't affect other projects)
$env:MAG_CODEBASE_ROOT = "C:\Projects\GameEngine"
$env:MAG_CHROMA_PERSIST_DIR = "C:\Users\YourName\AppData\Local\mag\chroma_game"
mag-index --clear

# Reindex UIFramework
$env:MAG_CODEBASE_ROOT = "C:\Projects\UIFramework"
$env:MAG_CHROMA_PERSIST_DIR = "C:\Users\YourName\AppData\Local\mag\chroma_ui"
mag-index --clear

# You can reindex without --clear to just update changed files
mag-index
```

## Project Isolation

Each project is completely isolated:

| Project | Database Location | Collection Name | Server Name |
|---------|------------------|-----------------|-------------|
| GameEngine | `chroma_game/` | `game_engine` | `mag-game-engine` |
| UIFramework | `chroma_ui/` | `ui_framework` | `mag-ui-framework` |
| NetworkingLib | `chroma_net/` | `networking_lib` | `mag-networking` |

Changes to one project **never affect** the others.

## Best Practices

### 1. Use Descriptive Names

```json
// Good - clear what each server is for
"mag-game-engine": { ... }
"mag-ui-framework": { ... }
"mag-tools-library": { ... }

// Avoid - generic names
"mag-project1": { ... }
"mag-csharp": { ... }
```

### 2. Organized Database Directories

```
C:\Users\YourName\AppData\Local\mag\
├── chroma_game\       # GameEngine database
├── chroma_ui\         # UIFramework database
├── chroma_network\    # NetworkingLib database
└── chroma_tools\      # ToolsLibrary database
```

### 3. Keep Collection Names Short

```json
// Good
"MAG_CHROMA_COLLECTION_NAME": "game_engine"

// Works but longer
"MAG_CHROMA_COLLECTION_NAME": "my_awesome_game_engine_codebase"
```

### 4. Document Your Projects

Create a reference file:

```json
// my_projects.json
{
  "projects": [
    {
      "name": "GameEngine",
      "path": "C:\\Projects\\GameEngine",
      "database": "chroma_game",
      "mcp_name": "mag-game-engine",
      "last_indexed": "2025-10-31"
    },
    {
      "name": "UIFramework",
      "path": "C:\\Projects\\UIFramework",
      "database": "chroma_ui",
      "mcp_name": "mag-ui-framework",
      "last_indexed": "2025-10-30"
    }
  ]
}
```

## Troubleshooting Multiple Projects

### Problem: Wrong Project Being Searched

**Symptom**: Asking about GameEngine returns UIFramework results

**Cause**: Projects using same database directory

**Fix**: Ensure each project has unique `MAG_CHROMA_PERSIST_DIR`

```powershell
# Check database directories are different
Get-Content "$env:APPDATA\Claude\claude_desktop_config.json" |
    ConvertFrom-Json |
    Select-Object -ExpandProperty mcpServers
```

### Problem: Server Not Appearing in Claude

**Symptom**: Only some MCP servers show up

**Cause**: JSON syntax error in config

**Fix**: Validate JSON

```powershell
# This will show errors if JSON is invalid
Get-Content "$env:APPDATA\Claude\claude_desktop_config.json" |
    ConvertFrom-Json
```

### Problem: Database Size Growing Too Large

**Symptom**: Slow searches, large disk usage

**Solution 1**: Archive old projects

```powershell
# Move unused project databases to archive
Move-Item "C:\Users\YourName\AppData\Local\mag\chroma_old_project" `
          "C:\Archive\mag\chroma_old_project"
```

**Solution 2**: Reduce chunk size for large projects

```json
"env": {
  "MAG_CHUNK_SIZE_TOKENS": "256",  // Smaller chunks
  "MAG_CHROMA_PERSIST_DIR": "..."
}
```

## Storage Considerations

### Typical Database Sizes

| Project Size | Files | Database Size |
|--------------|-------|---------------|
| Small (10K LOC) | 50 files | ~5 MB |
| Medium (100K LOC) | 500 files | ~50 MB |
| Large (1M LOC) | 5000 files | ~500 MB |

### Managing Disk Space

```powershell
# Check sizes of all project databases
Get-ChildItem "C:\Users\YourName\AppData\Local\mag\" -Directory |
    ForEach-Object {
        $size = (Get-ChildItem $_.FullName -Recurse |
                 Measure-Object -Property Length -Sum).Sum / 1MB
        [PSCustomObject]@{
            Project = $_.Name
            SizeMB = [math]::Round($size, 2)
        }
    } | Format-Table
```

## Advanced: Dynamic Project Loading

If you have many projects but only need a few at a time:

### Create Multiple Config Files

```
claude_config_game_dev.json     # GameEngine + UIFramework
claude_config_network_dev.json  # NetworkingLib + Tools
claude_config_all.json          # All projects
```

### Swap Configs as Needed

```powershell
# Use game development config
Copy-Item "claude_config_game_dev.json" `
          "$env:APPDATA\Claude\claude_desktop_config.json"

# Restart Claude Desktop
```

## Example: Team Scenario

Your team has multiple C# projects:

```
Team Projects:
├── GameEngine (main game code)
├── EditorTools (Unity editor extensions)
├── ServerBackend (multiplayer server)
└── SharedLibrary (common utilities)
```

Each developer can configure MAG for their active projects:

**Game Developer**:
```json
{
  "mcpServers": {
    "mag-game": { ... },
    "mag-shared": { ... }
  }
}
```

**Tools Developer**:
```json
{
  "mcpServers": {
    "mag-editor": { ... },
    "mag-shared": { ... }
  }
}
```

**Backend Developer**:
```json
{
  "mcpServers": {
    "mag-server": { ... },
    "mag-shared": { ... }
  }
}
```

Everyone has access to SharedLibrary, plus their domain-specific projects!

## Quick Reference Commands

```powershell
# Index new project
$env:MAG_CODEBASE_ROOT = "C:\Path\To\Project"
$env:MAG_CHROMA_PERSIST_DIR = "C:\Users\You\AppData\Local\mag\chroma_project"
mag-index -v

# Reindex existing project
$env:MAG_CODEBASE_ROOT = "C:\Path\To\Project"
$env:MAG_CHROMA_PERSIST_DIR = "C:\Users\You\AppData\Local\mag\chroma_project"
mag-index --clear

# Check project stats
mag-index --stats

# List all databases
Get-ChildItem "C:\Users\YourName\AppData\Local\mag\" -Directory
```

## Next Steps

- See [CLAUDE_SETUP.md](CLAUDE_SETUP.md) for basic setup
- See [INSTALLATION.md](INSTALLATION.md) for installation help
- Use [generate-multi-project-config.ps1](generate-multi-project-config.ps1) to create configs
