#!/bin/bash

# Configuration parameters (customize as needed)
MODEL_PATH="$(pwd)/models/gemma-3-27b-it-q4_0.gguf"
THREADS=8  # Recommended for M4 Pro
METAL_LAYERS=45  # Near maximum for 27B model on M4 Pro with enough RAM
PORT=5602
CONTEXT_SIZE=4096

echo "🚀 Setting up llama.cpp server for macOS with Metal acceleration"
echo "Model: $MODEL_PATH"

# Check if llama.cpp repository exists, if not clone it
if [ ! -d "llama.cpp" ]; then
    echo "📥 Cloning llama.cpp repository..."
    git clone https://github.com/ggerganov/llama.cpp.git
    cd llama.cpp
else
    cd llama.cpp
    echo "🔄 Updating llama.cpp repository..."
    git pull
fi

# Build llama.cpp with Metal support
echo "🔨 Building llama.cpp with Metal support..."
mkdir -p build
cd build
cmake .. -DLLAMA_METAL=ON
cmake --build . --config Release

# Check if model exists
cd ../..
if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ Error: Model file not found at $MODEL_PATH"
    echo "Please download the model and place it in the models directory"
    exit 1
fi

# Run the server using the compiled binary
echo "🚀 Starting llama.cpp server with Metal acceleration..."
echo "Using $THREADS threads and $METAL_LAYERS Metal layers"
echo "Server will be available at http://localhost:$PORT"

# Path to the compiled binary
LLAMA_SERVER_BIN="$(pwd)/llama.cpp/build/bin/llama-server"

# Check if the binary exists
if [ ! -f "$LLAMA_SERVER_BIN" ]; then
    echo "❌ Error: llama-server binary not found at $LLAMA_SERVER_BIN"
    echo "Build might have failed or the binary is in a different location"
    exit 1
fi

# Get help information to verify available options
echo "Checking available llama-server options:"
$LLAMA_SERVER_BIN --help | grep -E 'thread|gpu|port|host|model' || true

# Run the server using the compiled binary with updated parameters
$LLAMA_SERVER_BIN \
    --model "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port $PORT \
    --threads $THREADS \
    --gpu-layers $METAL_LAYERS \
    --chat-template chatml \
    --ctx-size $CONTEXT_SIZE \
    --parallel 1 \
    --cont-batching \
    --mlock