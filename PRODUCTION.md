# Production Deployment Guide
Norfain ReAct Agent - Production-Ready Flask Application

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose (recommended)
- Or: Python 3.13+, Redis, and local Ollama/cloud LLM API

### Option 1: Docker Compose (Easiest)

```bash
# Clone and setup
git clone <your-repo>
cd Financial_AI_ReAct_Agent

# Copy environment configuration
cp .env.example .env
# Edit .env with your settings (SECRET_KEY, LLM config, etc.)

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f web

# Access application
open http://localhost:5050
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install flask-compress flask-caching flask-limiter redis bleach python-dotenv waitress

# Start Redis
redis-server /opt/homebrew/etc/redis.conf  # macOS with Homebrew
# Or: docker run -p 6379:6379 redis:7-alpine

# Configure environment
cp .env.example .env
# Edit .env with production values

# Run application
python web_dashboard/app.py
# Or with Waitress (production):
waitress-serve --host=0.0.0.0 --port=5050 --threads=4 web_dashboard.app:create_app()
```

## 📋 Configuration

### Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `FLASK_ENV` | development | No | Environment: development/production |
| `FLASK_DEBUG` | false | No | Debug mode (disable in prod) |
| `SECRET_KEY` | (none) | **Yes** | Secret key for sessions |
| `CACHE_ENABLED` | true | No | Enable caching |
| `CACHE_TYPE` | redis | No | Cache backend: simple/redis |
| `CACHE_REDIS_URL` | redis://localhost:6379/0 | Conditional | Redis connection URL |
| `RATELIMIT_ENABLED` | true | No | Enable rate limiting |
| `ALLOWED_ORIGINS` | (dev defaults) | No | Comma-separated CORS origins |
| `AGENT_MODEL` | llama3.2:latest | No | Ollama model name |
| `SSB_API_BASE_URL` | https://data.ssb.no/api/v0 | No | SSB API endpoint |
| `LOG_LEVEL` | INFO | No | Logging level |
| `ADMIN_TOKEN` | (none) | No | Admin authentication token |

### Production Checklist

- [ ] Set strong `SECRET_KEY` (use `openssl rand -hex 32`)
- [ ] Set `FLASK_DEBUG=false`
- [ ] Set `SESSION_COOKIE_SECURE=true` (HTTPS)
- [ ] Configure `ALLOWED_ORIGINS` for your domains
- [ ] Use Redis for cache (`CACHE_TYPE=redis`)
- [ ] Set `ADMIN_TOKEN` for admin endpoints
- [ ] Enable HTTPS (use reverse proxy like Nginx/Traefik)
- [ ] Configure log rotation (logrotate or similar)
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Set up error tracking (Sentry)
- [ ] Configure database if storing user data
- [ ] Review and minimize CORS origins
- [ ] Enable HSTS in production

## 🔒 Security Hardening

### Recommended Security Headers (Nginx)

```nginx
location / {
    proxy_pass http://norfain-web:5050;

    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'nonce-${nonce}'; style-src 'self' 'unsafe-inline'; font-src 'self' fonts.gstatic.com;" always;
}
```

### Rate Limiting
- `/api/ask`: 30 requests/minute
- `/api/ssb-data`: 60 requests/minute
- `/api/admin/*`: 10 requests/minute
- Default: 100 requests/hour

### Authentication
- API endpoints currently open (research demo)
- For production, implement:
  - JWT tokens for user authentication
  - API keys for programmatic access
  - OAuth2 integration for single sign-on

## 📊 Monitoring & Observability

### Health Check
```
GET /health
```
Returns:
```json
{
  "status": "healthy",
  "components": {
    "agents": "loaded",
    "ssb_api": "connected",
    "cache": "enabled"
  },
  "metrics": {...},
  "timestamp": "2025-03-30T..."
}
```

### Metrics (Prometheus Format)
```
GET /api/metrics
```
Returns Prometheus-compatible metrics:
- `norfain_requests_total`
- `norfain_errors_total`
- `norfain_response_time_seconds`
- `norfain_cache_hits_total`
- `norfain_uptime_seconds`

### Logging
Logs written to `logs/app.log` with rotation:
- Format: `TIMESTAMP - LOGGER - LEVEL - MESSAGE`
- Levels: DEBUG, INFO, WARNING, ERROR
- External libs set to WARNING to reduce noise

### Recommended Monitoring Stack

```yaml
# docker-compose.monitoring.yml (excerpt)
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
  scrape_interval: 30s

grafana:
  image: grafana/grafana:latest
  dashboard provisioned for Norfain metrics
```

## 🔧 Scaling

### Vertical Scaling
Increase resources on single instance:
- CPU: More cores = more concurrent request handling
- RAM: 2GB minimum, 4GB+ recommended (Ollama uses ~3GB)
- Use Waitress with more threads: `--threads=8`

### Horizontal Scaling
Multiple app instances behind load balancer:

```yaml
# Kubernetes Deployment excerpt
replicas: 3
resources:
  requests:
    cpu: "1"
    memory: "2Gi"
  limits:
    cpu: "2"
    memory: "4Gi"

readinessProbe:
  httpGet:
    path: /health
    port: 5050
```

**Requirements for horizontal scaling:**
- Shared Redis for cache and rate limiting
- Stateless app design (sessions in Redis if needed)
- Load balancer with sticky sessions or JWT tokens
- External LLM API (not local Ollama) for multi-node

### Database Scaling
If adding PostgreSQL for user data:
- Use connection pooling (pgbouncer)
- Read replicas for reporting queries
- Index on frequently queried fields

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest tests/ --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # Your deployment commands
```

## 🐛 Troubleshooting

### Common Issues

**1. "Ollama not responding"**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags
# If not running:
ollama serve
# And in another terminal:
ollama pull llama3.2:latest
```

**2. Redis connection errors**
```bash
# Check Redis is running
redis-cli ping
# Should return "PONG"
# Start Redis if not running:
redis-server /opt/homebrew/etc/redis.conf
```

**3. Port 5050 already in use**
```bash
# Find process using port 5050
lsof -i :5050
# Kill it or change port:
export FLASK_PORT=5051
```

**4. Out of memory (Ollama)**
- Reduce agent concurrency (use single-threaded)
- Use cloud LLM API (Anthropic, OpenAI, Groq) instead
- Increase swap space temporarily:
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**5. Slow SSB API responses**
- Check internet connectivity
- SSB API may be rate limiting - check logs
- Increase cache TTL to reduce API calls
- Use Redis cache to share across instances

### Performance Tuning

```bash
# Profile the application
python -m cProfile -o profile.prof -m web_dashboard.app
# Visualize with:
snakeviz profile.prof

# Monitor with py-spy (sampling profiler)
py-spy top --pid <pid>
```

## 🔄 Backup & Recovery

### Redis Backup
Redis persistence configured (AOF + RDB snapshots):
```bash
# Redis data stored in: /opt/homebrew/var/db/redis/
# Backup:
cp /opt/homebrew/var/db/redis/dump.rdb /backup/redis-$(date +%Y%m%d).rdb

# Restore:
cp /backup/redis-20250330.rdb /opt/homebrew/var/db/redis/dump.rdb
redis-cli shutdown
redis-server /opt/homebrew/etc/redis.conf
```

### Application Data Backup
- If using PostgreSQL: `pg_dump` regular backups
- Cache is ephemeral - can be rebuilt
- Logs: Rotate and archive weekly

## 🚨 Incident Response

### Application Down
1. Check logs: `tail -f logs/app.log`
2. Check health: `curl http://localhost:5050/health`
3. Check process: `ps aux | grep app.py`
4. Restart: `docker-compose restart web` or restart service
5. Check disk space: `df -h`
6. Check memory: `free -h`

### Performance Degradation
1. Check Redis: `redis-cli info memory`
2. Check Ollama: `curl http://localhost:11434/api/tags`
3. Check metrics: Grafana dashboard or `/api/metrics`
4. Scale up: Increase threads or replicas
5. Profile: `py-spy record -o profile.svg --pid <pid>`

### Security Incident
1. Revoke all API tokens
2. Rotate `SECRET_KEY` and `ADMIN_TOKEN`
3. Check access logs for unauthorized access
4. Review deployed code for unauthorized changes
5. Consider temporary shutdown if breach confirmed

## 📈 Performance Benchmarks

### Target Metrics (Production)

| Metric | Target | Current | Notes |
|--------|--------|---------|-------|
| **Response Time (P95)** | < 5s | ~12s | Agent processing dominates |
| **Cache Hit Rate** | > 80% | ~60% | SSB data cached 24h |
| **Uptime** | 99.9% | 99% | Target with monitoring |
| **Concurrent Users** | 100+ | 5-10 | Limited by Ollama |
| **Startup Time** | < 10s | ~5s | Agent initialization |

### Bottlenecks & Optimizations

**Current Bottleneck**: LLM inference (8-12s per query)
**Solutions**:
1. Use faster LLM (Groq Cloud - 500 tok/s vs Ollama ~15 tok/s)
2. Implement streaming responses (SSE)
3. Add task queue (Celery) for async processing
4. Cache frequent questions (embedding similarity)

## 🔮 Future Improvements

1. **Async FastAPI Migration** - 2-3x throughput improvement
2. **Vector Cache** - Semantic caching of similar questions
3. **Multi-Model Support** - Let users choose Claude/GPT/Llama
4. **User Accounts** - Save history, preferences, goals
5. **Advanced Analytics** - More sophisticated budget analysis
6. **Mobile App** - React Native frontend
7. **Real-time SSB Updates** - Webhook-based data refresh
8. **A/B Testing Framework** - Compare agent strategies
9. **External Data Sources** - Yahoo Finance, Macrotrends
10. **Explainability Dashboard** - Visualize agent reasoning patterns

---

Built with ❤️ at NMBU, Norway
Making Financial AI Transparent and Trustworthy
