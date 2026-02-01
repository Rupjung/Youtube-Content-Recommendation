FROM python:3.10-slim

# System deps
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama (binary only)
RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app

# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create runtime dirs
RUN mkdir -p outputs static templates

EXPOSE 8000

CMD ["sh", "-c", "ollama serve & uvicorn app:app --host 0.0.0.0 --port 8000"]
