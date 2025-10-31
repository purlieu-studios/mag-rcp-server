@echo off
REM MAG MCP Server - Clean Reinstallation Script
REM Removes existing installation and reinstalls from scratch

echo ================================================
echo   MAG MCP Server - Clean Reinstall
echo ================================================
echo.
echo This will remove the existing installation and reinstall.
echo.
set /p CONFIRM="Continue? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Installation cancelled.
    exit /b 0
)

echo.
echo Cleaning previous installation...

REM Remove virtual environment
if exist "venv" (
    echo   Removing virtual environment...
    rmdir /s /q venv
)

REM Remove build artifacts
if exist "build" (
    echo   Removing build directory...
    rmdir /s /q build
)

if exist "dist" (
    echo   Removing dist directory...
    rmdir /s /q dist
)

REM Remove egg-info
for /d %%i in (*.egg-info) do (
    echo   Removing %%i...
    rmdir /s /q "%%i"
)

REM Remove __pycache__ directories
echo   Removing __pycache__ directories...
for /d /r %%i in (__pycache__) do (
    if exist "%%i" rmdir /s /q "%%i"
)

echo.
echo Cleanup complete. Starting fresh installation...
echo.

REM Run installation script
if "%1"=="--dev" (
    call install.bat --dev
) else (
    call install.bat
)

echo.
echo Reinstallation complete!
