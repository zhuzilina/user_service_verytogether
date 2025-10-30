# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Use Aliyun mirrors for faster package downloads
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Configure pip to use Tsinghua mirrors for faster downloads
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Install pip-tools first
COPY requirements/ requirements/
RUN pip install --no-cache-dir pip-tools

# Install Python dependencies using pip-tools
# Use production requirements for Docker builds
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy project files
COPY . .

# Create non-root user
RUN addgroup --system django \
    && adduser --system --ingroup django django

# Create logs directory with proper permissions
RUN mkdir -p logs \
    && chown -R django:django /app

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