# Dockerfile for Google Cloud Run - Cloud Trading Bot
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and Google Cloud SDK
RUN apt-get update && apt-get install -y \
    curl \
    python3-pip \
    gnupg \
    && curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-449.0.0-linux-x86_64.tar.gz \
    && tar -xf google-cloud-sdk-449.0.0-linux-x86_64.tar.gz \
    && ./google-cloud-sdk/install.sh \
    && rm google-cloud-sdk-449.0.0-linux-x86_64.tar.gz \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/google-cloud-sdk/bin:${PATH}"

# Copy requirements and install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ /app/backend/

# Create non-root user
RUN adduser --disabled-password --gecos '' --uid 1001 tradingbot
RUN chown -R tradingbot:tradingbot /app
USER tradingbot

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check - update this to your main entrypoint!
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import backend.config; print('Health check passed')" || exit 1

# Run the main backend (update this if your bot entrypoint is different)
CMD ["python", "backend/main.py"]
