# Multi-stage Dockerfile for TikTok Video Automation Bot
# Target: < 700MB final image

# Stage 1: Build dependencies
FROM python:3.11-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime image
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome for Selenium (headless)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app user for security
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /app

# Copy application code
COPY --chown=app:app . .

# Create necessary directories
RUN mkdir -p assets/bg assets/overlays output logs temp backups

# Set timezone
ENV TZ=UTC

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import yaml; print('OK')" || exit 1

# Default command
CMD ["./scheduler.sh"]
