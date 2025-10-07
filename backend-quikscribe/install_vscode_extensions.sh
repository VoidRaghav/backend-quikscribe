#!/bin/bash

# VS Code Extensions Installation Script for QuikScribe Backend
# Run this script to install all recommended extensions

echo "Installing VS Code Extensions for QuikScribe Backend Development..."

# Check if VS Code is installed
if ! command -v code &> /dev/null; then
    echo "VS Code command line interface not found."
    echo "Please install VS Code first, then run this script again."
    echo "You can download VS Code from: https://code.visualstudio.com/"
    exit 1
fi

# Core Python Development Extensions
echo "Installing Python development extensions..."
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension kevinrose.python-indent
code --install-extension njpwerner.autodocstring

# FastAPI & Web Development
echo "Installing FastAPI and web development extensions..."
code --install-extension tamasfe.even-better-toml
code --install-extension humao.rest-client
code --install-extension rangav.vscode-thunder-client

# TypeScript/JavaScript Development
echo "Installing TypeScript and JavaScript extensions..."
code --install-extension oven.bun-vscode
code --install-extension dsznajder.es7-react-js-snippets

# Database & ORM
echo "Installing database extensions..."
code --install-extension mtxr.sqltools
code --install-extension mtxr.sqltools-postgresql

# Environment & Configuration
echo "Installing configuration extensions..."
code --install-extension mikestead.dotenv
code --install-extension redhat.vscode-yaml
code --install-extension tamasfe.even-better-toml

# Docker & Kubernetes
echo "Installing Docker and Kubernetes extensions..."
code --install-extension ms-azuretools.vscode-docker
code --install-extension ms-kubernetes-tools.vscode-kubernetes-tools

# Git & Version Control
echo "Installing Git extensions..."
code --install-extension eamodio.gitlens
code --install-extension donjayamanne.githistory

# Code Quality & Formatting
echo "Installing code quality extensions..."
code --install-extension ms-python.black-formatter
code --install-extension ms-python.isort
code --install-extension esbenp.prettier-vscode
code --install-extension dbaeumer.vscode-eslint

# Testing & Debugging
echo "Installing testing extensions..."
code --install-extension littlefoxteam.vscode-python-test-adapter
code --install-extension ryanluker.vscode-coverage-gutters

# Productivity & Utilities
echo "Installing productivity extensions..."
code --install-extension formulahendry.auto-rename-tag
code --install-extension coenraads.bracket-pair-colorizer-2
code --install-extension christian-kohler.path-intellisense
code --install-extension pkief.material-icon-theme

echo ""
echo "All VS Code extensions have been installed!"
echo ""
echo "Next steps:"
echo "1. Restart VS Code"
echo "2. Open your QuikScribe backend project"
echo "3. Select Python interpreter: .venv_quikscribe/bin/python"
echo "4. Install Python packages: pip install -r requirements.txt"
echo ""
echo "Recommended VS Code settings have been saved to .vscode/settings.json"
