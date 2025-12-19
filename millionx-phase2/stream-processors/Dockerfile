FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download embedding model at build time to avoid download delays at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 faust && chown -R faust:faust /app
USER faust

# Expose Faust web UI port
EXPOSE 6066

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:6066/health', timeout=3)"

# Default command (can be overridden in docker-compose)
CMD ["faust", "-A", "privacy_shield", "worker", "-l", "info"]
