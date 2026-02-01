# Multi-stage build: First stage for Ollama setup
FROM python:3.10-slim AS ollama-stage

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    zstd \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama server and pull model at build time
RUN ollama serve & sleep 10 && ollama pull llama3.2:3b

# Second stage: Final app image
FROM python:3.10-slim

# Copy Ollama from first stage
COPY --from=ollama-stage /usr/local/bin/ollama /usr/local/bin/ollama
COPY --from=ollama-stage /root/.ollama /root/.ollama

# Install system dependencies (minimal for final stage)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache layers: Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code after dependencies
COPY . .

EXPOSE 8000

# Run Ollama server and FastAPI (model already pulled at build time)
CMD ["sh", "-c", "ollama serve & sleep 5 && uvicorn app:app --host 0.0.0.0 --port 8000"]