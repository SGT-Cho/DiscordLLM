#!/bin/bash

# Script to run the Discord bot with proper environment variables for macOS
ROOT_DIR=$(pwd)
VENV_DIR="$ROOT_DIR/mac-native/venv"

echo "🤖 Starting Discord Bot with proper local environment variables..."

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Set the environment variables
export MCP_API="http://localhost:5601"
export QDRANT_URL="http://localhost:5600"
export SEARXNG_URL="http://localhost:5578"
export BOT_PREFIX="/"  # Explicitly set prefix to /

# Check if DISCORD_TOKEN is set
if [ -z "$DISCORD_TOKEN" ]; then
    echo "⚠️ DISCORD_TOKEN environment variable not set."
    echo "Please enter your Discord bot token:"
    read -r DISCORD_TOKEN
    export DISCORD_TOKEN
fi

# Run the Discord bot
cd "$ROOT_DIR/discord-bot"
echo "Starting Discord bot with:"
echo "- MCP API: $MCP_API"
echo "- Qdrant URL: $QDRANT_URL"
echo "- SearxNG URL: $SEARXNG_URL"
echo "- Command prefix: $BOT_PREFIX"
echo "- Token: ${DISCORD_TOKEN:0:5}...${DISCORD_TOKEN: -5}"  # Show first 5 and last 5 chars for safety

# Test if MCP server is reachable
echo "Testing connection to MCP server..."
curl -s -o /dev/null -w "MCP Server status: %{http_code}\n" $MCP_API || echo "⚠️ Failed to connect to MCP server"

echo "Starting Discord bot now..."
python main.py