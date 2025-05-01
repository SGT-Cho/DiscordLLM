#!/bin/bash

# Activate the conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate discord-llm

# Change to the project directory
cd "$(dirname "$0")/.."

# Run the MCP server
echo "Starting MCP server..."
python mcp-server/main.py