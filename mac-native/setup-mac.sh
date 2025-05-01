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

# Install dependencies for all components
echo "📦 Installing dependencies..."

# MCP Server dependencies
echo "Installing MCP Server dependencies..."
pip install -r "$ROOT_DIR/mcp-server/requirements.txt"

# Agent dependencies
echo "Installing Agent dependencies..."
pip install -r "$ROOT_DIR/agent/requirements.txt"

# Document indexer dependencies
echo "Installing Document Indexer dependencies..."
pip install -r "$ROOT_DIR/indexer/requirements.txt"

# Discord bot dependencies
echo "Installing Discord Bot dependencies..."
pip install -r "$ROOT_DIR/discord-bot/requirements.txt"

# Make run scripts executable
chmod +x "$ROOT_DIR/mac-native/run-llama-server.sh"
chmod +x "$ROOT_DIR/mac-native/run-services.sh"

echo "✅ Setup complete! Use './mac-native/run-services.sh' to start all services."