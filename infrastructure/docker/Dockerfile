# Dockerfile for ECS Strategy Engine
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements_Version9.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install additional AWS dependencies
RUN pip install --no-cache-dir boto3 watchtower

# Copy application code
COPY backend/ /app/backend/
COPY aws/ /app/aws/

# Create non-root user
RUN adduser --disabled-password --gecos '' --uid 1001 tradingbot
RUN chown -R tradingbot:tradingbot /app
USER tradingbot

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import backend.config; print('Health check passed')" || exit 1

# Run the strategy engine
CMD ["python", "aws/strategy_engine.py"]