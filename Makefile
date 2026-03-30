# Norfain ReAct Agent - Makefile for Development & Deployment
.PHONY: help install run test docker-build docker-run clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies and setup virtual environment
	python -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	./venv/bin/pip install flask-compress flask-caching flask-limiter redis bleach python-dotenv waitress
	@echo "✅ Installation complete! Activate with: source venv/bin/activate"

run: ## Run the Flask development server
	./venv/bin/python web_dashboard/app.py

run-prod: ## Run with Waitress production server
	./venv/bin/waitress-serve --host=0.0.0.0 --port=5050 --threads=4 web_dashboard.app:create_app

test: ## Run tests
	./venv/bin/pytest tests/ -v --cov=src --cov-report=html

lint: ## Run code linting
	./venv/bin/pip install flake8 black isort
	./venv/bin/flake8 src/ web_dashboard/ --count --select=E9,F63,F7,F82 --show-source --statistics
	./venv/bin/black --check src/ web_dashboard/
	./venv/bin/isort --check-only src/ web_dashboard/

format: ## Format code with black and isort
	./venv/bin/black src/ web_dashboard/
	./venv/bin/isort src/ web_dashboard/

docker-build: ## Build Docker image
	docker build -t norfain:latest .

docker-run: ## Run with Docker Compose
	docker-compose up -d
	@echo "✅ Application starting... Visit http://localhost:5050"
	@echo "   Health check: curl http://localhost:5050/health"

docker-stop: ## Stop Docker Compose services
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f web

clean: ## Clean up temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	@echo "✅ Clean complete"

# Ollama commands (requires Ollama installed locally)
ollama-pull: ## Pull Llama 3.2 model for local LLM
	ollama pull llama3.2:latest

ollama-run: ## Run Ollama server locally
	ollama serve

# Database commands (if using PostgreSQL)
db-init: ## Initialize database (placeholder)
	@echo "Run alembic upgrade head to initialize database"

db-migrate: ## Create a new migration
	./venv/bin/alembic revision --autogenerate -m "migration message"

db-upgrade: ## Apply migrations
	./venv/bin/alembic upgrade head

# Monitoring
monitor-start: ## Start monitoring stack (Grafana + Prometheus)
	docker-compose -f docker-compose.monitoring.yml up -d

monitor-stop: ## Stop monitoring stack
	docker-compose -f docker-compose.monitoring.yml down
