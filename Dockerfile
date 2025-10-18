# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Install pip-tools first
COPY requirements/ requirements/
RUN pip install --no-cache-dir pip-tools

# Install Python dependencies using pip-tools
# Use production requirements for Docker builds
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy project files
COPY . .

# Create logs directory
RUN mkdir -p logs

# Create non-root user
RUN addgroup --system django \
    && adduser --system --ingroup django django

# Change ownership of the app directory
RUN chown -R django:django /app

# Switch to non-root user
USER django

# Collect static files (if any)
RUN python manage.py collectstatic --noinput || true

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health/ || exit 1

# Expose port
EXPOSE 8001

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-", "UserService.wsgi:application"]