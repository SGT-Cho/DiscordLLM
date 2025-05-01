# Discord LLM Bot

Discord LLM Bot is an integrated solution that provides question answering, web search, and information retrieval capabilities for Discord servers using powerful local or cloud-based AI models.

**Key Features:**
- 🤖 Freely converse with local Gemma 3 models or cloud-based OpenAI/Anthropic AI
- 🔍 Provide up-to-date information through web search functionality
- 📚 Document search and Q&A through vector database (RAG)
- 🔄 Choose from various AI providers (local LLM, OpenAI, Anthropic Claude)
- 🐳 Easy deployment and management with Docker containers

## Table of Contents

- [System Requirements](#system-requirements)
- [Architecture Overview](#architecture-overview)
- [Installation](#installation)
  - [Installing Docker](#1-installing-docker)
  - [Downloading the Project](#2-downloading-the-project)
  - [Environment Setup](#3-environment-setup)
  - [Downloading Models](#4-downloading-models-for-local-llm)
  - [Discord Bot Setup](#5-discord-bot-setup)
- [Running the Application](#running-the-application)
  - [Using the Deployment Script](#using-the-deployment-script)
  - [Checking Logs](#checking-logs)
  - [Stopping Services](#stopping-services)
- [Usage Guide](#usage-guide)
  - [Discord Commands](#discord-commands)
  - [Utilizing Web Search](#utilizing-web-search)
- [Changing LLM Providers](#changing-llm-providers)
  - [Using Local LLM](#using-local-llm)
  - [Using OpenAI API](#using-openai-api)
  - [Using Anthropic Claude API](#using-anthropic-claude-api)
- [Advanced Configuration](#advanced-configuration)
  - [Hardware Acceleration Settings](#hardware-acceleration-settings)
  - [Changing Models](#changing-models)
  - [Resource Limitations](#resource-limitations)
- [Troubleshooting](#troubleshooting)
- [Development Information](#development-information)
- [License](#license)

## System Requirements

### For Docker Deployment (Recommended)
- Docker and Docker Compose installed
- Internet connection
- Minimum 8GB RAM, 16GB+ recommended
- At least 20GB of disk space
- Discord bot token

### Additional Requirements for Local LLM
- NVIDIA GPU (with CUDA support) or Apple Silicon Mac (with Metal support)
- Minimum 16GB RAM, 24GB+ recommended
- At least 30GB of disk space for model files

## Architecture Overview

The Discord LLM Bot consists of the following components:

1. **Discord Bot**: Communicates with the Discord API and processes user messages.
2. **MCP Server**: Model Context Protocol server that interfaces with various LLM providers.
3. **Llama.cpp Server**: High-performance inference server that runs local LLM (only used in local LLM mode).
4. **Qdrant**: Vector database that supports RAG (Retrieval-Augmented Generation).
5. **SearxNG**: Private meta-search engine that provides web search functionality.

The system is managed through Docker Compose, with all services running as containers.

## Installation

### 1. Installing Docker

Docker and Docker Compose must be installed on your system.

#### Linux (Ubuntu/Debian):
```bash
# Install Docker
sudo apt-get update
sudo apt-get install docker.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Start and enable Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

#### macOS:
Install [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac/)

#### Windows:
Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows/)

### 2. Downloading the Project

```bash
# Clone the project using Git
git clone https://github.com/SGT-Cho/DiscordLLM.git
cd DiscordLLM
```

### 3. Environment Setup

Copy the `.env.example` file to `.env` and modify the necessary settings:

```bash
cp .env.example .env
```

Open the `.env` file with a text editor and set the following required items:

- `DISCORD_TOKEN`: Bot token created in the Discord Developer Portal
- `LLM_PROVIDER`: Choose LLM provider (`local`, `openai`, `anthropic`)

Additional settings for external APIs:
- For OpenAI: Set `OPENAI_API_KEY` and `OPENAI_MODEL`
- For Anthropic: Set `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL`

Additional settings for local LLM:
- `THREADS`: Number of CPU threads to use
- `METAL_LAYERS`: Number of layers for Metal acceleration on Apple Silicon Macs
- `GPU_LAYERS`: Number of CUDA acceleration layers for NVIDIA GPUs

### 4. Downloading Models (for Local LLM)

To use a local LLM, you need to download model files:

1. Create a `models` directory:
```bash
mkdir -p models
```

2. Download the Gemma 3 27B Instruct model. You can download GGUF format models from [Hugging Face](https://huggingface.co/google/gemma-3-27b-it/tree/gguf):
```bash
# Example: Download Q4_0 quantized model
wget https://huggingface.co/google/gemma-3-27b-it/resolve/gguf/gemma-3-27b-it-q4_0.gguf -P models/
```

Other options: You can choose different quantized models to balance accuracy and memory requirements:
- `gemma-3-27b-it-q5_0.gguf`: Higher accuracy, uses more memory
- `gemma-3-27b-it-q3_k_m.gguf`: Lower accuracy, uses less memory

### 5. Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click "New Application" and enter a name for your bot.
3. Go to the "Bot" section and click "Add Bot".
4. Click "Reset Token" to generate a new token and copy it.
5. Paste this token into the `DISCORD_TOKEN` variable in your `.env` file.
6. Go to "OAuth2" → "URL Generator" and select the following permissions:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Read Message History`, `Add Reactions`, `Attach Files`, `Embed Links`, `Use Slash Commands`
7. Use the generated URL to invite the bot to your Discord server.

## Running the Application

### Using the Deployment Script

Make the deployment script executable and start it:

```bash
chmod +x deploy.sh
./deploy.sh start
```

The script will check your settings and start the necessary containers. Depending on the LLM provider setting, it will:

- `LLM_PROVIDER=local`: Run all services including the local Llama.cpp server
- `LLM_PROVIDER=openai` or `LLM_PROVIDER=anthropic`: Run services excluding the Llama.cpp server

### Checking Logs

You can check service logs to monitor proper operation:

```bash
# Check logs for all services
./deploy.sh logs

# Check logs for a specific service (e.g., Discord bot)
./deploy.sh logs discord-bot
```

### Stopping Services

To stop services, run:

```bash
./deploy.sh stop
```

## Usage Guide

### Discord Commands

You can use the bot in Discord servers as follows:

- **General questions**: Mention the bot and input your question.
  ```
  @LLMBot Write a Python code to calculate the Fibonacci sequence
  ```

- **Web search questions**: Input questions that need factual or up-to-date information.
  ```
  @LLMBot What's the weather like today?
  @LLMBot What's the current Tesla stock price?
  ```

### Utilizing Web Search

The bot automatically performs web searches for questions with the following patterns:
- Questions about recent news or information
- Questions requiring fact-checking
- Questions about specific dates, times, prices, etc.

Search results are included as part of the response, with source links provided at the end of the response.

## Changing LLM Providers

### Using Local LLM

To use a local LLM, set the following in your `.env` file:

```
LLM_PROVIDER=local
MODEL_PATH=/models/gemma-3-27b-it-q4_0.gguf
```

In this mode, the model file must be in the `models` directory.

### Using OpenAI API

To use the OpenAI API, set the following in your `.env` file:

```
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o  # or another model
```

### Using Anthropic Claude API

To use the Anthropic Claude API, set the following in your `.env` file:

```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-opus-20240229  # or another model
```

## Advanced Configuration

### Hardware Acceleration Settings

To optimize hardware acceleration when using local LLM:

- **For NVIDIA GPU**:
  ```
  GPU_LAYERS=33  # Adjust to match model layers
  ```

- **For Apple Silicon Mac**:
  ```
  METAL_LAYERS=32  # Adjust to match model layers
  ```

- **CPU Thread Optimization**:
  ```
  THREADS=8  # Set to the number of available physical cores
  ```

### Changing Models

To use a different model:

1. Download the model file to the `models` directory.
2. Update the `MODEL_PATH` variable in your `.env` file:
   ```
   MODEL_PATH=/models/your-new-model.gguf
   ```

### Resource Limitations

To limit memory usage, you can adjust resource limits for the `llama-server` service in the `docker-compose.yml` file:

```yaml
deploy:
  resources:
    limits:
      memory: 12G  # Adjust memory limit
```

## Troubleshooting

### Common Issues and Solutions

1. **Discord bot not responding**
   - Check logs with `./deploy.sh logs discord-bot`
   - Verify that the Discord bot token is set correctly
   - Check that the bot has the necessary permissions

2. **Local LLM server errors**
   - Check logs with `./deploy.sh logs llama-server`
   - Verify that the model file is in the correct location
   - Check that your system has enough memory
   - Verify that GPU/Metal settings are correct

3. **API key errors**
   - Check that the API key is correctly set in the `.env` file
   - Ensure there are no extra spaces or quotes in the API key

4. **Out of memory errors**
   - Try using a lower quantization model (e.g., q3_k_m)
   - Check and adjust Docker resource limits
   - Close unnecessary background processes

5. **Search functionality not working**
   - Check logs with `./deploy.sh logs searxng` and `./deploy.sh logs mcp-server`
   - Verify your internet connection

### Checking Logs and Debugging

The best way to troubleshoot issues is to check the logs:

```bash
# Check logs for a specific service
./deploy.sh logs service-name

# Check real-time logs
./deploy.sh logs -f service-name
```

## Development Information

This project consists of the following components:

- **Discord Bot**: Discord interface using Discord.py
- **MCP Server**: FastAPI-based API server
- **Llama.cpp Server**: High-performance inference server written in C++
- **Qdrant**: Vector database (for RAG functionality)
- **SearxNG**: Private meta-search engine

If you want to contribute to the code or participate in development, refer to the README and source code in each directory.

## License

[MIT License](LICENSE)

---

If you have any issues or need help, please file an issue or contact the project maintainer.