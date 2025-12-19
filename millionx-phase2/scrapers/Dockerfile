FROM python:3.11-slim

LABEL maintainer="MillionX Team"
LABEL description="Production scraper container with Playwright and anti-bot measures"

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker cache optimization)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium && \
    playwright install-deps chromium

# Copy application code
COPY shared/ ./shared/
COPY social/ ./social/
COPY market/ ./market/

# Create non-root user for security
RUN useradd -m -u 1000 scraper && \
    chown -R scraper:scraper /app

USER scraper

# Default environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "from kafka import KafkaProducer; KafkaProducer(bootstrap_servers='${KAFKA_BOOTSTRAP_SERVERS}', request_timeout_ms=5000).close()" || exit 1

# Default command (override in K8s CronJob)
CMD ["python", "social/tiktok_scraper.py"]
