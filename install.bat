@echo off
REM MAG MCP Server - Windows Installation Script (Batch)
REM Simple installation script for users who prefer batch files

setlocal EnableDelayedExpansion

echo ================================================
echo   MAG MCP Server - Installation Script
echo ================================================
echo.

REM Check Python installation
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo   X Error: Python not found in PATH
    echo   Please install Python 3.14+ from https://www.python.org/
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo   √ Found: !PYTHON_VERSION!

REM Create virtual environment
echo.
echo [2/4] Setting up virtual environment...
if not exist "venv" (
    python -m venv venv
    echo   √ Created virtual environment
) else (
    echo   √ Virtual environment already exists
)

REM Activate virtual environment
echo.
echo [3/4] Activating virtual environment...
call venv\Scripts\activate.bat
echo   √ Virtual environment activated

REM Install package
echo.
echo [4/4] Installing MAG MCP Server...

REM Check for dev mode argument
if "%1"=="--dev" (
    echo   Installing in development mode with dev dependencies...
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"
) else (
    echo   Installing in production mode...
    python -m pip install --upgrade pip
    python -m pip install -e .
)

if errorlevel 1 (
    echo   X Installation failed
    exit /b 1
)

echo   √ Installation completed successfully

REM Display success message
echo.
echo ================================================
echo   Installation Complete!
echo ================================================
echo.
echo To use MAG MCP Server:
echo   1. Activate the virtual environment:
echo      venv\Scripts\activate.bat
echo.
echo   2. Run the indexing script:
echo      mag-index
echo.
echo   3. Start the MCP server:
echo      mag-server
echo.
echo Configuration:
echo   Set environment variables or create .env file:
echo     set MAG_CODEBASE_ROOT=C:\path\to\your\csharp\project
echo     set MAG_CHROMA_PERSIST_DIR=C:\path\to\vector\db
echo.

if "%1"=="--dev" (
    echo Development Mode:
    echo   Run tests:
    echo     pytest tests/
    echo.
    echo   Check coverage:
    echo     pytest --cov=mag --cov-report=html
    echo.
)

echo For more information, see README.md
echo.

endlocal
