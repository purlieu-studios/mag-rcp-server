#!/usr/bin/env pwsh
# MAG MCP Server - Claude Desktop Configuration Generator
# Generates a ready-to-use Claude Desktop configuration

param(
    [Parameter(Mandatory=$false)]
    [string]$CodebasePath = "",

    [Parameter(Mandatory=$false)]
    [string]$ChromaPath = "$env:LOCALAPPDATA\mag\chroma",

    [Parameter(Mandatory=$false)]
    [string]$OllamaHost = "http://localhost:11434",

    [switch]$CopyToClipboard = $false,

    [switch]$OpenConfig = $false
)

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  MAG MCP Server - Config Generator" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get current directory (where the script is)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ScriptDir "venv\Scripts\python.exe"

# Validate Python path
if (-not (Test-Path $VenvPython)) {
    Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run .\install.ps1 first" -ForegroundColor Yellow
    exit 1
}

Write-Host "Virtual environment found: $VenvPython" -ForegroundColor Green

# Get codebase path if not provided
if ([string]::IsNullOrEmpty($CodebasePath)) {
    Write-Host ""
    Write-Host "Enter the path to your C# codebase:" -ForegroundColor Yellow
    $CodebasePath = Read-Host "Codebase path"

    if ([string]::IsNullOrEmpty($CodebasePath)) {
        Write-Host "Error: Codebase path is required!" -ForegroundColor Red
        exit 1
    }
}

# Validate codebase path
if (-not (Test-Path $CodebasePath)) {
    Write-Host "Warning: Codebase path does not exist: $CodebasePath" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y") {
        exit 1
    }
}

# Convert paths to absolute and escape backslashes for JSON
$VenvPythonJson = (Resolve-Path $VenvPython).Path -replace '\\', '\\'
$CodebasePathJson = (Resolve-Path -Path $CodebasePath -ErrorAction SilentlyContinue).Path
if ([string]::IsNullOrEmpty($CodebasePathJson)) {
    $CodebasePathJson = $CodebasePath
}
$CodebasePathJson = $CodebasePathJson -replace '\\', '\\'
$ChromaPathJson = $ChromaPath -replace '\\', '\\'

Write-Host ""
Write-Host "Configuration Details:" -ForegroundColor Cyan
Write-Host "  Python: $VenvPython" -ForegroundColor Gray
Write-Host "  Codebase: $CodebasePath" -ForegroundColor Gray
Write-Host "  Chroma DB: $ChromaPath" -ForegroundColor Gray
Write-Host "  Ollama: $OllamaHost" -ForegroundColor Gray
Write-Host ""

# Generate configuration
$config = @"
{
  "mcpServers": {
    "mag-csharp-rag": {
      "command": "$VenvPythonJson",
      "args": [
        "-m",
        "mag.server"
      ],
      "env": {
        "MAG_CODEBASE_ROOT": "$CodebasePathJson",
        "MAG_CHROMA_PERSIST_DIR": "$ChromaPathJson",
        "MAG_OLLAMA_HOST": "$OllamaHost",
        "MAG_EMBEDDING_MODEL": "nomic-embed-text",
        "MAG_LLM_MODEL": "codestral"
      }
    }
  }
}
"@

# Display configuration
Write-Host "Generated Configuration:" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Gray
Write-Host $config -ForegroundColor White
Write-Host "================================================" -ForegroundColor Gray
Write-Host ""

# Save to file
$OutputFile = Join-Path $ScriptDir "claude_desktop_config_generated.json"
$config | Out-File -FilePath $OutputFile -Encoding UTF8
Write-Host "✓ Saved to: $OutputFile" -ForegroundColor Green

# Copy to clipboard if requested
if ($CopyToClipboard) {
    $config | Set-Clipboard
    Write-Host "✓ Copied to clipboard" -ForegroundColor Green
}

# Show Claude Desktop config location
$ClaudeConfigPath = "$env:APPDATA\Claude\claude_desktop_config.json"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Copy this configuration to Claude Desktop config file:" -ForegroundColor White
Write-Host "   $ClaudeConfigPath" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. If you have existing MCP servers, merge this into your config" -ForegroundColor White
Write-Host ""
Write-Host "3. Restart Claude Desktop" -ForegroundColor White
Write-Host ""

# Offer to open config file
if ($OpenConfig) {
    if (Test-Path $ClaudeConfigPath) {
        Write-Host "Opening Claude Desktop config file..." -ForegroundColor Yellow
        notepad $ClaudeConfigPath
    } else {
        Write-Host "Claude Desktop config file not found. Creating it..." -ForegroundColor Yellow
        New-Item -ItemType File -Path $ClaudeConfigPath -Force | Out-Null
        $config | Out-File -FilePath $ClaudeConfigPath -Encoding UTF8
        Write-Host "✓ Created config file: $ClaudeConfigPath" -ForegroundColor Green
        notepad $ClaudeConfigPath
    }
} else {
    Write-Host "Quick commands:" -ForegroundColor Cyan
    Write-Host "  # Open Claude Desktop config" -ForegroundColor Gray
    Write-Host "  notepad `"$ClaudeConfigPath`"" -ForegroundColor White
    Write-Host ""
    Write-Host "  # Or auto-open with:" -ForegroundColor Gray
    Write-Host "  .\generate-claude-config.ps1 -OpenConfig" -ForegroundColor White
    Write-Host ""
    Write-Host "  # Copy to clipboard:" -ForegroundColor Gray
    Write-Host "  .\generate-claude-config.ps1 -CopyToClipboard" -ForegroundColor White
}

Write-Host ""
Write-Host "Before using with Claude Desktop:" -ForegroundColor Yellow
Write-Host "  1. Make sure Ollama is running" -ForegroundColor Gray
Write-Host "  2. Index your codebase: mag-index --codebase `"$CodebasePath`"" -ForegroundColor Gray
Write-Host "  3. Restart Claude Desktop" -ForegroundColor Gray
Write-Host ""
