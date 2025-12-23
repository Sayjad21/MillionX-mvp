FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for ai-core
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Install ai-core dependencies on startup (if volume is mounted)
# This ensures pandas, numpy, sklearn are available
CMD /bin/bash -c "if [ -f /ai-core/requirements.txt ]; then pip install --no-cache-dir -r /ai-core/requirements.txt; fi && uvicorn main:app --host 0.0.0.0 --port 8000"
