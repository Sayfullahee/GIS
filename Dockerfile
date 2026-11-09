# =============================================================================
# CHER-CDSS Decision-Support System Containerfile
# Specification: Master Implementation Scaffold v4.1 (October 2026)
# =============================================================================

FROM python:3.12-slim-bookworm

# Prevent interactive prompts during apt-get
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install essential system geospatial and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition and install packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose FastAPI REST service port
EXPOSE 8000

# Default healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Launch the FastAPI Web GIS decision-support server
CMD ["python", "run_dashboard.py"]
