#!/bin/bash

# Script to run all Discord LLM services natively on macOS Apple Silicon
ROOT_DIR=$(pwd)
VENV_DIR="$ROOT_DIR/mac-native/venv"
PORT_QDRANT=5600
PORT_MCP=5601
PORT_LLAMA=5602
PORT_SEARX=5578

# Function to start services in a new terminal window
start_service() {
    local title=$1
    local command=$2
    osascript -e "tell application \"Terminal\" to do script \"cd '$ROOT_DIR' && source '$VENV_DIR/bin/activate' && echo '$title' && $command\""
}

# Function to check if a service is running on a port
is_port_in_use() {
    lsof -i:$1 &> /dev/null
    if [ $? -eq 0 ]; then
        echo "Service already running on port $1"
        return 0
    else
        return 1
    fi
}

echo "🚀 Starting Discord LLM services on macOS..."

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found. Run setup-mac.sh first."
    exit 1
fi

# 1. Start Qdrant (using Docker)
if ! is_port_in_use $PORT_QDRANT; then
    echo "📊 Starting Qdrant vector database..."
    start_service "QDRANT SERVER" "docker run -d --name qdrant -p $PORT_QDRANT:6333 -v qdrant_data:/qdrant/storage qdrant/qdrant"
    sleep 2
fi

# 2. Start SearxNG (using Docker)
if ! is_port_in_use $PORT_SEARX; then
    echo "🔍 Starting SearxNG search engine..."
    start_service "SEARXNG SERVER" "docker run -d --name searxng -p $PORT_SEARX:8080 searxng/searxng"
    sleep 2
fi

# 3. Start llama.cpp server with Metal acceleration
if ! is_port_in_use $PORT_LLAMA; then
    echo "🧠 Starting llama.cpp server with Metal acceleration..."
    start_service "LLAMA.CPP SERVER" "$ROOT_DIR/mac-native/run-llama-server.sh"
    sleep 5
fi

# 4. Start MCP Server
if ! is_port_in_use $PORT_MCP; then
    echo "🔌 Starting MCP Server..."
    export QDRANT_URL="http://localhost:$PORT_QDRANT"
    export LLAMA_SERVER_URL="http://localhost:$PORT_LLAMA"
    export SEARXNG_URL="http://localhost:$PORT_SEARX"
    start_service "MCP SERVER" "cd $ROOT_DIR/mcp-server && python main.py"
    sleep 2
fi

# 5. Start Discord bot
echo "🤖 Starting Discord Bot..."
export MCP_API="http://localhost:$PORT_MCP"
export QDRANT_URL="http://localhost:$PORT_QDRANT"
export SEARXNG_URL="http://localhost:$PORT_SEARX"
# Check if DISCORD_TOKEN is set
if [ -z "$DISCORD_TOKEN" ]; then
    echo "⚠️ DISCORD_TOKEN environment variable not set."
    echo "Please set your Discord token by running: export DISCORD_TOKEN=your_token"
    read -p "Enter your Discord bot token: " DISCORD_TOKEN
    export DISCORD_TOKEN
fi
start_service "DISCORD BOT" "cd $ROOT_DIR/discord-bot && python main.py"

echo "✅ All services started!"
echo "- Qdrant is running on port $PORT_QDRANT"
echo "- MCP Server is running on port $PORT_MCP"
echo "- llama.cpp server is running on port $PORT_LLAMA"
echo "- SearxNG is running on port $PORT_SEARX"
echo ""
echo "🛑 To stop services, close the terminal windows or run: docker stop qdrant searxng"