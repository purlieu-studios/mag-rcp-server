# MAG MCP Server - Installation Guide

This document explains how to install and manage the MAG MCP Server on Windows.

## Quick Start

### Option 1: PowerShell (Recommended)
```powershell
# Standard installation
.\install.ps1

# Development installation (includes test tools)
.\install.ps1 -DevMode

# Clean installation (removes existing files first)
.\install.ps1 -Clean

# Clean development installation
.\install.ps1 -Clean -DevMode
```

### Option 2: Batch File
```cmd
# Standard installation
install.bat

# Development installation
install.bat --dev
```

## Installation Scripts

### `install.ps1` (PowerShell)
Full-featured installation script with the following options:

**Parameters:**
- `-DevMode`: Installs with development dependencies (pytest, mypy, ruff, etc.)
- `-Clean`: Removes existing installation before reinstalling

**What it does:**
1. Checks Python installation (requires Python 3.14+)
2. Optionally cleans previous installation
3. Creates a virtual environment (`venv/`)
4. Activates the virtual environment
5. Installs the package in editable mode

**Example usage:**
```powershell
# First time installation
.\install.ps1

# Reinstall after code changes
.\install.ps1 -Clean

# Set up for development
.\install.ps1 -DevMode -Clean
```

### `install.bat` (Batch)
Simpler alternative for users who prefer batch files or have PowerShell restrictions.

**Arguments:**
- `--dev`: Installs with development dependencies

**Example usage:**
```cmd
# Standard installation
install.bat

# Development installation
install.bat --dev
```

### `reinstall.bat` (Batch)
Quick script for clean reinstallation. Prompts for confirmation before removing files.

**Example usage:**
```cmd
# Clean reinstall for production
reinstall.bat

# Clean reinstall for development
reinstall.bat --dev
```

## After Installation

### 1. Activate the Virtual Environment

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Command Prompt:**
```cmd
venv\Scripts\activate.bat
```

You should see `(venv)` in your prompt indicating the virtual environment is active.

### 2. Configure Environment Variables

Create a `.env` file in the project root or set environment variables:

```bash
MAG_CODEBASE_ROOT=C:\path\to\your\csharp\project
MAG_CHROMA_PERSIST_DIR=C:\path\to\vector\db
MAG_OLLAMA_HOST=http://localhost:11434
MAG_EMBEDDING_MODEL=nomic-embed-text
MAG_LLM_MODEL=codestral
```

**PowerShell:**
```powershell
$env:MAG_CODEBASE_ROOT = "C:\path\to\your\csharp\project"
$env:MAG_CHROMA_PERSIST_DIR = "C:\Users\YourName\AppData\Local\mag\chroma"
```

**Command Prompt:**
```cmd
set MAG_CODEBASE_ROOT=C:\path\to\your\csharp\project
set MAG_CHROMA_PERSIST_DIR=C:\Users\YourName\AppData\Local\mag\chroma
```

### 3. Verify Installation

```bash
# Check installed commands
mag-index --help
mag-server --help

# Check Ollama connection
mag-index --check-ollama

# View index statistics
mag-index --stats
```

## Usage

### Index a Codebase

```bash
# Index the configured codebase
mag-index

# Index a specific codebase
mag-index --codebase C:\path\to\project

# Clear and reindex
mag-index --clear

# Verbose output
mag-index -v
```

### Run the MCP Server

```bash
mag-server
```

The server will start and listen for MCP client connections via stdio.

## Development Workflow

If you installed with `-DevMode` or `--dev`:

### Run Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=mag --cov-report=html

# Run specific test file
pytest tests/test_retrieval/test_vector_store.py

# Run with verbose output
pytest -v
```

### Code Quality
```bash
# Type checking
mypy src/

# Linting
ruff check src/ tests/

# Format code
ruff format src/ tests/
```

### After Making Changes

1. **If you modified dependencies** (pyproject.toml):
   ```powershell
   # PowerShell
   .\install.ps1 -Clean

   # Or batch
   reinstall.bat --dev
   ```

2. **If you only modified code**:
   Changes are automatically reflected (editable install)

3. **Run tests to verify**:
   ```bash
   pytest tests/
   ```

## Troubleshooting

### PowerShell Execution Policy Error

If you see "cannot be loaded because running scripts is disabled":

```powershell
# Check current policy
Get-ExecutionPolicy

# Allow scripts for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run install script
.\install.ps1
```

### Python Not Found

Ensure Python 3.14+ is installed and in PATH:
1. Download from https://www.python.org/
2. During installation, check "Add Python to PATH"
3. Restart your terminal

### Virtual Environment Issues

If you encounter venv activation issues:

```powershell
# Remove and recreate
Remove-Item -Recurse -Force venv
.\install.ps1
```

### Ollama Connection Issues

Ensure Ollama is running:
```bash
# Check if Ollama is available
mag-index --check-ollama

# Start Ollama (if not running)
ollama serve
```

## Uninstallation

To completely remove the installation:

```powershell
# Remove virtual environment
Remove-Item -Recurse -Force venv

# Remove build artifacts
Remove-Item -Recurse -Force build, dist, *.egg-info

# Remove database (optional)
Remove-Item -Recurse -Force $env:MAG_CHROMA_PERSIST_DIR
```

## Additional Resources

- [README.md](README.md) - Project overview and features
- [pyproject.toml](pyproject.toml) - Project configuration and dependencies
- [Ollama Documentation](https://ollama.ai/) - For embedding model setup
