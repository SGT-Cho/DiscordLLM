#!/bin/bash

# Mac-native setup script for Discord LLM project on Apple Silicon
ROOT_DIR=$(pwd)
VENV_DIR="$ROOT_DIR/mac-native/venv"

echo "🍎 Setting up Discord LLM project for macOS on Apple Silicon (M4 Pro)"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 Creating Python virtual environment..."
    mkdir -p "$VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Update pip
echo "📦 Updating pip..."
pip install --upgrade pip

# Install dependencies for all components
echo "📦 Installing dependencies..."

# First install some common dependencies to prevent conflicts
echo "Installing common dependencies..."
pip install pydantic==2.5.2 python-dotenv==1.0.0 requests==2.31.0

# MCP Server dependencies
echo "Installing MCP Server dependencies..."
pip install fastapi==0.104.1 uvicorn==0.23.2 httpx==0.25.2 qdrant-client

# Discord bot dependencies
echo "Installing Discord Bot dependencies..."
pip install discord.py==2.3.2

# Install torch and related packages for Mac M4
echo "Installing PyTorch for Apple Silicon..."
pip install torch torchvision

# Install sentence-transformers
echo "Installing sentence-transformers..."
pip install sentence-transformers>=2.2.2 pypdf==4.0.1 transformers

# Agent dependencies
echo "Installing LangChain agent dependencies..."
pip install langchain-core>=0.1.9
pip install langchain>=0.1.0
pip install langchain-community>=0.0.13
pip install langchain-openai>=0.0.5

# Make run scripts executable
chmod +x "$ROOT_DIR/mac-native/run-llama-server.sh"
chmod +x "$ROOT_DIR/mac-native/run-services.sh"

echo "✅ Setup complete! Use './mac-native/run-services.sh' to start all services."