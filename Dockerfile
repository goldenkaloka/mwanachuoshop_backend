# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies including GDAL
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        binutils \
        libproj-dev \
        gdal-bin \
        libgdal-dev \
        postgis \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .
# Create non-root user for security and ensure media/staticfiles directories are owned by appuser
RUN adduser --disabled-password --gecos '' appuser \
    && mkdir -p /app/media \
    && mkdir -p /app/staticfiles \
    && chown -R appuser:appuser /app/media \
    && chown -R appuser:appuser /app/staticfiles
USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# (Optional) Declare media as a volume
VOLUME ["/app/media"]

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "core.wsgi:application"] 