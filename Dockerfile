# Norfain ReAct Agent - Production Docker Image
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama (optional - for local LLM)
# Uncomment if you want Ollama in the container
# RUN curl -fsSL https://ollama.ai/install.sh | sh && \
#     ollama pull llama3.2:latest

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir flask-compress flask-caching flask-limiter redis bleach python-dotenv waitress

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data/ssb_cache

# Set environment variables
ENV FLASK_ENV=production \
    FLASK_DEBUG=false \
    CACHE_ENABLED=true \
    CACHE_TYPE=redis \
    CACHE_REDIS_URL=redis://redis:6379/0 \
    RATELIMIT_ENABLED=true \
    RATELIMIT_STORAGE_URL=redis://redis:6379/0 \
    LOG_LEVEL=INFO

# Expose port
EXPOSE 5050

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5050/health || exit 1

# Run with Waitress (production WSGI server)
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5050", "--threads=4", "web_dashboard.app:create_app()"]
