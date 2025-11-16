FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libc-dev \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY src/ ./src/

# Create non-root user and sessions directory
RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /app/sessions \
    && chown -R appuser:appuser /app \
    && chmod 755 /app/sessions
USER appuser

# Command to run the application
CMD ["python", "-m", "src.main"]
