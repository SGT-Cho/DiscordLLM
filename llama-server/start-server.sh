#!/bin/bash

# Get the number of threads from environment variable or use default
THREADS=${THREADS:-4}
METAL_LAYERS=${METAL_LAYERS:-32}

# Check if model exists
MODEL_PATH=${MODEL_PATH:-"/models/gemma-3-27b-it-qat-q4_0.gguf"}
if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model file not found at $MODEL_PATH"
    echo "Please ensure the GGUF model file is mounted in the /models directory"
    exit 1
fi

echo "Starting llama.cpp server with model: $MODEL_PATH"

# Check if MPS is available (for macOS)
USE_MPS=0
if [ "$(uname)" = "Darwin" ] && [ "$METAL_LAYERS" -gt 0 ]; then
    # Check for Metal device
    system_profiler SPDisplaysDataType 2>/dev/null | grep -q "Metal: Supported"
    if [ $? -eq 0 ]; then
        USE_MPS=1
        echo "MPS (Metal Performance Shaders) acceleration detected and enabled!"
        echo "Using $THREADS threads and $METAL_LAYERS Metal layers with MPS acceleration"
    else
        echo "Metal is not supported on this device, using CPU only"
        echo "Using $THREADS threads (CPU only)"
    fi
else
    echo "Using $THREADS threads and $METAL_LAYERS Metal layers"
fi

# Debug: List directories to verify binaries exist
echo "Checking for server binaries:"
ls -la /app/bin/ || echo "Directory /app/bin/ does not exist"
ls -la /app/llama.cpp/build/bin/ || echo "Directory /app/llama.cpp/build/bin/ does not exist"

# Try to find the server binary in different locations
SERVER_PATH=""
if [ -f "/app/bin/llama-server" ]; then
    echo "Found server at /app/bin/llama-server"
    SERVER_PATH="/app/bin/llama-server"
elif [ -f "/app/bin/server" ]; then
    echo "Found server at /app/bin/server"
    SERVER_PATH="/app/bin/server"
elif [ -f "/app/llama.cpp/build/bin/server" ]; then
    echo "Found server at /app/llama.cpp/build/bin/server"
    SERVER_PATH="/app/llama.cpp/build/bin/server"
elif [ -f "/app/llama.cpp/build/bin/llama-server" ]; then
    echo "Found server at /app/llama.cpp/build/bin/llama-server"
    SERVER_PATH="/app/llama.cpp/build/bin/llama-server"
else
    echo "Error: Server binary not found in any expected location!"
    exit 1
fi

# Run the server with binary directly
echo "Executing server from: $SERVER_PATH"
$SERVER_PATH \
    --model "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port 5602 \
    --threads "$THREADS" \
    --n-gpu-layers "$METAL_LAYERS" \
    --chat-template chatml \
    --ctx-size 4096 \
    --parallel 1 \
    --cont-batching \
    --mlock

# If server crashes, keep container running for debugging
if [ $? -ne 0 ]; then
    echo "Server crashed. Container will keep running for debugging."
    tail -f /dev/null
fi