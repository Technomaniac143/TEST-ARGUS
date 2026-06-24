FROM python:3.12-slim

WORKDIR /app

# Install system dependencies required for compiling some Python libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies first to leverage caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application files
COPY backend/ ./backend/

# Expose port (documented only, Railway overrides this)
EXPOSE 8000

# Start command dynamically binding to the port provided by Railway ($PORT)
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
