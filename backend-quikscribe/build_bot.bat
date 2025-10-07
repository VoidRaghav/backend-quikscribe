@echo off
echo 🔨 Building Meeting Bot Docker Image
echo =====================================

REM Navigate to bot directory
cd google_bot

REM Build the Docker image
echo Building Docker image...
docker build -t meeting-bot:latest .

if %ERRORLEVEL% EQU 0 (
    echo ✅ Docker image built successfully!
    echo Image name: meeting-bot:latest
    
    echo.
    echo 📋 Image details:
    docker images meeting-bot:latest
    
    echo.
    echo 🚀 Ready to run concurrent meetings!
    echo Each meeting will get a unique port automatically.
) else (
    echo ❌ Failed to build Docker image
    exit /b 1
)
