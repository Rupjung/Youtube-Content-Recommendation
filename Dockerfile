FROM python:3.10-slim

# Install system dependencies FIRST
RUN apt-get update && apt-get install -y \
    curl \
    zstd \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama (binary only)
RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Runtime dirs (important for your FastAPI error)
RUN mkdir -p outputs static templates

EXPOSE 8000

CMD ["sh", "-c", "ollama serve & uvicorn app:app --host 0.0.0.0 --port 8000"]
