@echo off
setlocal enabledelayedexpansion

:: --- Configuration (Set by setup.ps1) ---
set "TV_EXE=[[TRADINGVIEW_EXE]]"
set "TV_PORTABLE_DIR=[[TV_PORTABLE_DIR]]"
set "TV_SOURCE_DIR=[[TV_SOURCE_DIR]]"
set "BROWSER_EXE=[[BROWSER_EXE]]"
set "BROWSER_URL=https://www.bitunix.com"
set "WORKSPACE_DIR=%~dp0"
set "CDP_PORT=9222"

echo Starting Bit Unix Trading MCP Environment...

:: TVPortable check
if not exist "!TV_EXE!" (
    echo TradingView not found at !TV_EXE!
    if exist "!TV_SOURCE_DIR!" (
        echo Creating TVPortable from source...
        robocopy "!TV_SOURCE_DIR!" "!TV_PORTABLE_DIR!" /E /NFL /NDL
        echo Copying completed.
    ) else (
        echo ERROR: TradingView source not found. Please run setup.ps1 again.
        pause
        exit /b 1
    )
)

:: Start TradingView with CDP
echo Launching TradingView on port !CDP_PORT!...
start "" "!TV_EXE!" --remote-debugging-port=!CDP_PORT!

:: Wait for CDP
echo Waiting 15 seconds for TradingView to be ready...
timeout /t 15 /nobreak >nul

:: Port check
netstat -ano | findstr ":!CDP_PORT!" >nul
if errorlevel 1 (
    echo ERROR: Port !CDP_PORT! is not open. Please check if TradingView started correctly.
    pause
    exit /b 1
)

echo Port !CDP_PORT! active.
echo Launching Claude Code...
start "Claude Code - Bit Unix Trading MCP" cmd /k "cd /d "!WORKSPACE_DIR!" && claude --dangerously-skip-permissions ."

echo Opening Browser...
start "" "!BROWSER_EXE!" "!BROWSER_URL!"

echo Setup complete. Happy trading!
