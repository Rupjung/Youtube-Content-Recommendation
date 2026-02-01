FROM python:3.10-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pull lightweight model
RUN ollama pull llama3.2:3b

EXPOSE 8000

CMD ollama serve & uvicorn app:app --host 0.0.0.0 --port 8000
