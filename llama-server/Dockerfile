FROM ubuntu:22.04 AS builder

# Install build dependencies including libcurl
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3 \
    python3-pip \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone llama.cpp repository
WORKDIR /app
RUN git clone https://github.com/ggerganov/llama.cpp.git && \
    cd llama.cpp && \
    git checkout master && \
    mkdir build && \
    cd build && \
    cmake .. -DLLAMA_CURL=ON && \
    cmake --build . --config Release

FROM ubuntu:22.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    libcurl4 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built binaries from builder stage
COPY --from=builder /app/llama.cpp/build/bin /app/bin
COPY --from=builder /app/llama.cpp/models /app/models

# Copy Python server code - updating path to include all llama.cpp code
COPY --from=builder /app/llama.cpp /app/llama.cpp

# Install Python dependencies directly (not using requirements file)
RUN pip3 install 'fastapi>=0.95.2' 'uvicorn>=0.22.0' 'sse-starlette>=1.6.1' 'pydantic>=2.0' 'starlette>=0.27.0'

# Copy the startup script
COPY ./start-server.sh /app/start-server.sh
RUN chmod +x /app/start-server.sh

EXPOSE 5602

# Run the server
CMD ["/app/start-server.sh"]