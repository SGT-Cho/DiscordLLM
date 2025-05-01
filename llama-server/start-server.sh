#!/bin/bash

# Get the number of threads from environment variable or use default
THREADS=${THREADS:-4}
METAL_LAYERS=${METAL_LAYERS:-32}

# Check if model exists
MODEL_PATH="/models/gemma-3-27b-it-qat-q4_0.gguf"
if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model file not found at $MODEL_PATH"
    echo "Please ensure the GGUF model file is mounted in the /models directory"
    exit 1
fi

echo "Starting llama.cpp server with model: $MODEL_PATH"
echo "Using $THREADS threads and $METAL_LAYERS Metal layers"

cd /app

# Start the server with OpenAI API compatibility, configured for Apple Silicon
python3 -m server.app \
    --model "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port 5602 \
    --n-threads "$THREADS" \
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