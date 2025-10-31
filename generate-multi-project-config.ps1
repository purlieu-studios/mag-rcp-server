#!/usr/bin/env pwsh
# MAG MCP Server - Multi-Project Configuration Generator
# Generates Claude Desktop configurations for multiple C# projects

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectName,

    [Parameter(Mandatory=$true)]
    [string]$CodebasePath,

    [Parameter(Mandatory=$false)]
    [string]$ChromaDir = "",

    [Parameter(Mandatory=$false)]
    [string]$OutputFile = "claude_config_multi.json",

    [Parameter(Mandatory=$false)]
    [string]$AppendTo = "",

    [switch]$OpenConfig = $false
)

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Multi-Project Config Generator" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ScriptDir "venv\Scripts\python.exe"

# Validate Python path
if (-not (Test-Path $VenvPython)) {
    Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run .\install.ps1 first" -ForegroundColor Yellow
    exit 1
}

# Validate codebase path
if (-not (Test-Path $CodebasePath)) {
    Write-Host "Warning: Codebase path does not exist: $CodebasePath" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y") {
        exit 1
    }
}

# Generate default chroma directory if not provided
if ([string]::IsNullOrEmpty($ChromaDir)) {
    $safeName = $ProjectName.ToLower() -replace '[^a-z0-9]', '_'
    $ChromaDir = "$env:LOCALAPPDATA\mag\chroma_$safeName"
}

# Convert paths for JSON
$VenvPythonJson = (Resolve-Path $VenvPython).Path -replace '\\', '\\'
$CodebasePathJson = (Resolve-Path -Path $CodebasePath -ErrorAction SilentlyContinue).Path
if ([string]::IsNullOrEmpty($CodebasePathJson)) {
    $CodebasePathJson = $CodebasePath
}
$CodebasePathJson = $CodebasePathJson -replace '\\', '\\'
$ChromaDirJson = $ChromaDir -replace '\\', '\\'

# Generate server name (kebab-case)
$serverName = "mag-" + ($ProjectName.ToLower() -replace '[^a-z0-9]+', '-')

# Generate collection name (snake_case)
$collectionName = $ProjectName.ToLower() -replace '[^a-z0-9]+', '_'

Write-Host "Configuration for project:" -ForegroundColor Cyan
Write-Host "  Project Name: $ProjectName" -ForegroundColor White
Write-Host "  Server Name: $serverName" -ForegroundColor Gray
Write-Host "  Codebase: $CodebasePath" -ForegroundColor Gray
Write-Host "  Database: $ChromaDir" -ForegroundColor Gray
Write-Host "  Collection: $collectionName" -ForegroundColor Gray
Write-Host ""

# Create single server configuration
$serverConfig = @"
    "$serverName": {
      "command": "$VenvPythonJson",
      "args": [
        "-m",
        "mag.server"
      ],
      "env": {
        "MAG_CODEBASE_ROOT": "$CodebasePathJson",
        "MAG_CHROMA_PERSIST_DIR": "$ChromaDirJson",
        "MAG_CHROMA_COLLECTION_NAME": "$collectionName",
        "MAG_OLLAMA_HOST": "http://localhost:11434",
        "MAG_EMBEDDING_MODEL": "nomic-embed-text",
        "MAG_LLM_MODEL": "codestral"
      }
    }
"@

# Handle appending to existing file
if (-not [string]::IsNullOrEmpty($AppendTo) -and (Test-Path $AppendTo)) {
    Write-Host "Appending to existing config: $AppendTo" -ForegroundColor Yellow

    try {
        $existingJson = Get-Content $AppendTo -Raw | ConvertFrom-Json

        # Check if server already exists
        if ($existingJson.mcpServers.PSObject.Properties.Name -contains $serverName) {
            Write-Host "Warning: Server '$serverName' already exists in config!" -ForegroundColor Yellow
            $overwrite = Read-Host "Overwrite? (y/N)"
            if ($overwrite -ne "y") {
                Write-Host "Cancelled." -ForegroundColor Red
                exit 1
            }
        }

        # Add new server
        $existingJson.mcpServers | Add-Member -MemberType NoteProperty -Name $serverName -Value @{
            command = $VenvPythonJson
            args = @("-m", "mag.server")
            env = @{
                MAG_CODEBASE_ROOT = $CodebasePathJson
                MAG_CHROMA_PERSIST_DIR = $ChromaDirJson
                MAG_CHROMA_COLLECTION_NAME = $collectionName
                MAG_OLLAMA_HOST = "http://localhost:11434"
                MAG_EMBEDDING_MODEL = "nomic-embed-text"
                MAG_LLM_MODEL = "codestral"
            }
        } -Force

        # Save back
        $existingJson | ConvertTo-Json -Depth 10 | Out-File -FilePath $AppendTo -Encoding UTF8

        Write-Host "✓ Added '$serverName' to $AppendTo" -ForegroundColor Green
        Write-Host ""

        # Show current servers
        Write-Host "Current servers in config:" -ForegroundColor Cyan
        $existingJson.mcpServers.PSObject.Properties.Name | ForEach-Object {
            Write-Host "  - $_" -ForegroundColor White
        }

        $OutputFile = $AppendTo

    } catch {
        Write-Host "Error parsing existing config: $_" -ForegroundColor Red
        exit 1
    }

} else {
    # Create new config file
    $fullConfig = @"
{
  "mcpServers": {
$serverConfig
  }
}
"@

    $fullConfig | Out-File -FilePath $OutputFile -Encoding UTF8
    Write-Host "✓ Created new config: $OutputFile" -ForegroundColor Green
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Configuration Generated!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# Show indexing command
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Index this project:" -ForegroundColor White
Write-Host "   `$env:MAG_CODEBASE_ROOT = `"$CodebasePath`"" -ForegroundColor Yellow
Write-Host "   `$env:MAG_CHROMA_PERSIST_DIR = `"$ChromaDir`"" -ForegroundColor Yellow
Write-Host "   mag-index -v" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Copy config to Claude Desktop:" -ForegroundColor White
Write-Host "   Copy contents of:" -ForegroundColor Gray
Write-Host "   $OutputFile" -ForegroundColor Yellow
Write-Host "   To:" -ForegroundColor Gray
Write-Host "   `$env:APPDATA\Claude\claude_desktop_config.json" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Restart Claude Desktop" -ForegroundColor White
Write-Host ""

# Offer to add another project
Write-Host "To add another project:" -ForegroundColor Cyan
Write-Host "  .\generate-multi-project-config.ps1 ``" -ForegroundColor White
Write-Host "    -ProjectName `"AnotherProject`" ``" -ForegroundColor White
Write-Host "    -CodebasePath `"C:\Path\To\Another`" ``" -ForegroundColor White
Write-Host "    -AppendTo `"$OutputFile`"" -ForegroundColor White
Write-Host ""

# Open config if requested
if ($OpenConfig) {
    Write-Host "Opening config file..." -ForegroundColor Yellow
    notepad $OutputFile
}

# Show quick index script
Write-Host "Quick index script for this project:" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Gray
$indexScript = @"
# Save as index-$($ProjectName.ToLower()).ps1
`$env:MAG_CODEBASE_ROOT = "$CodebasePath"
`$env:MAG_CHROMA_PERSIST_DIR = "$ChromaDir"
mag-index -v
"@
Write-Host $indexScript -ForegroundColor White
Write-Host "================================================" -ForegroundColor Gray
Write-Host ""

# Save index script
$indexScriptFile = "index-$($ProjectName.ToLower()).ps1"
$indexScript | Out-File -FilePath $indexScriptFile -Encoding UTF8
Write-Host "✓ Saved index script to: $indexScriptFile" -ForegroundColor Green
Write-Host ""
