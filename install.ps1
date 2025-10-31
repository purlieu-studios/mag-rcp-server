#!/usr/bin/env pwsh
# MAG MCP Server - Windows Installation Script
# This script installs or reinstalls the MAG MCP server with all dependencies

param(
    [switch]$DevMode = $false,
    [switch]$Clean = $false
)

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  MAG MCP Server - Installation Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Found: $pythonVersion" -ForegroundColor Green

    # Check if Python 3.14+
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 14)) {
            Write-Host "  ⚠ Warning: Python 3.14+ is recommended (found $major.$minor)" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "  ✗ Error: Python not found in PATH" -ForegroundColor Red
    Write-Host "  Please install Python 3.14+ from https://www.python.org/" -ForegroundColor Red
    exit 1
}

# Clean installation if requested
if ($Clean) {
    Write-Host ""
    Write-Host "[2/5] Cleaning previous installation..." -ForegroundColor Yellow
    if (Test-Path "venv") {
        Remove-Item -Recurse -Force "venv"
        Write-Host "  ✓ Removed virtual environment" -ForegroundColor Green
    }
    if (Test-Path "*.egg-info") {
        Remove-Item -Recurse -Force "*.egg-info"
        Write-Host "  ✓ Removed egg-info directories" -ForegroundColor Green
    }
    if (Test-Path "build") {
        Remove-Item -Recurse -Force "build"
        Write-Host "  ✓ Removed build directory" -ForegroundColor Green
    }
    if (Test-Path "dist") {
        Remove-Item -Recurse -Force "dist"
        Write-Host "  ✓ Removed dist directory" -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "[2/5] Checking for clean installation..." -ForegroundColor Yellow
    Write-Host "  (Use -Clean flag to remove existing installation)" -ForegroundColor Gray
}

# Create virtual environment
Write-Host ""
Write-Host "[3/5] Setting up virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "  ✓ Created virtual environment" -ForegroundColor Green
} else {
    Write-Host "  ✓ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "[4/5] Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
Write-Host "  ✓ Virtual environment activated" -ForegroundColor Green

# Install package
Write-Host ""
Write-Host "[5/5] Installing MAG MCP Server..." -ForegroundColor Yellow

if ($DevMode) {
    Write-Host "  Installing in development mode with dev dependencies..." -ForegroundColor Cyan
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"
} else {
    Write-Host "  Installing in production mode..." -ForegroundColor Cyan
    python -m pip install --upgrade pip
    python -m pip install -e .
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Installation completed successfully" -ForegroundColor Green
} else {
    Write-Host "  ✗ Installation failed" -ForegroundColor Red
    exit 1
}

# Display success message
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "To use MAG MCP Server:" -ForegroundColor White
Write-Host "  1. Activate the virtual environment:" -ForegroundColor Gray
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Run the indexing script:" -ForegroundColor Gray
Write-Host "     mag-index" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. Start the MCP server:" -ForegroundColor Gray
Write-Host "     mag-server" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor White
Write-Host "  Set environment variables or create .env file:" -ForegroundColor Gray
Write-Host "    MAG_CODEBASE_ROOT=C:\path\to\your\csharp\project" -ForegroundColor Cyan
Write-Host "    MAG_CHROMA_PERSIST_DIR=C:\path\to\vector\db" -ForegroundColor Cyan
Write-Host ""

if ($DevMode) {
    Write-Host "Development Mode:" -ForegroundColor White
    Write-Host "  Run tests:" -ForegroundColor Gray
    Write-Host "    pytest tests/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Check coverage:" -ForegroundColor Gray
    Write-Host "    pytest --cov=mag --cov-report=html" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "For more information, see README.md" -ForegroundColor Gray
Write-Host ""
