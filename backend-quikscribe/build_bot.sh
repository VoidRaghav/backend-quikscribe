#!/bin/bash

echo "🔨 Building Meeting Bot Docker Image"
echo "====================================="

# Navigate to bot directory
cd google_bot

# Build the Docker image
echo "Building Docker image..."
docker build -t meeting-bot:latest .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    echo "Image name: meeting-bot:latest"
    
    # Show image details
    echo ""
    echo "📋 Image details:"
    docker images meeting-bot:latest
    
    echo ""
    echo "🚀 Ready to run concurrent meetings!"
    echo "Each meeting will get a unique port automatically."
else
    echo "❌ Failed to build Docker image"
    exit 1
fi
