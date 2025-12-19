FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY snowflake_batch_sink.py .

# Run as non-root user
RUN useradd -m -u 1000 snowflake && chown -R snowflake:snowflake /app
USER snowflake

# Run the batch sink
CMD ["python", "snowflake_batch_sink.py"]
