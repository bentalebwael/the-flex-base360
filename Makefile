.PHONY: help setup install clean dev-back dev-front docker-up docker-down docker-clean test lint format back front

# Default target - show help
help:
	@echo "Base360 Project Management"
	@echo "=========================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  make setup          - Initial project setup (install all dependencies)"
	@echo "  make install        - Install dependencies for backend and frontend"
	@echo "  make uv-install     - Install Python backend dependencies only"
	@echo ""
	@echo "Development Commands:"
	@echo "  make back           - Run backend development server (alias: dev-back)"
	@echo "  make front          - Run frontend development server (alias: dev-front)"
	@echo "  make dev            - Run both backend and frontend (in parallel)"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up      - Start all services with Docker Compose"
	@echo "  make docker-down    - Stop all Docker services"
	@echo "  make docker-clean   - Stop services and remove volumes"
	@echo "  make docker-logs    - Follow Docker logs"
	@echo "  make docker-restart - Restart all Docker services"
	@echo ""
	@echo "Database Commands:"
	@echo "  make db-init        - Initialize database with schema and seed data"
	@echo "  make db-reset       - Reset database (drop and recreate)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - Run linters for backend and frontend"
	@echo "  make format         - Format code (Python and JavaScript/TypeScript)"
	@echo "  make pre-commit     - Install pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-back      - Run backend tests only"
	@echo "  make test-front     - Run frontend tests only"
	@echo ""
	@echo "Build Commands:"
	@echo "  make build          - Build both backend and frontend"
	@echo "  make build-back     - Build backend Docker image"
	@echo "  make build-front    - Build frontend for production"
	@echo ""
	@echo "Utilities:"
	@echo "  make health         - Check health of all services"
	@echo "  make status         - Show Docker service status"
	@echo "  make clean          - Remove build artifacts and caches"
	@echo "  make clean-all      - Deep clean (including dependencies)"
	@echo "  make reset          - Full project reset"
	@echo ""
	@echo "Nix Commands:"
	@echo "  make nix-update     - Update Nix flake inputs"
	@echo "  make nix-check      - Check Nix flake validity"
	@echo "  make shell-back     - Enter Nix backend development shell"
	@echo "  make shell-front    - Enter Nix frontend development shell"

# Initial project setup
setup: install pre-commit
	@echo "✅ Setup complete! Run 'make dev' to start development."

# Install all dependencies
install: uv-install
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ All dependencies installed!"

# Install Python backend dependencies
uv-install:
	@echo "📦 Installing backend dependencies..."
	cd backend && uv sync

# Original backend command (kept for compatibility)
back:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Original frontend command (kept for compatibility)
front:
	cd frontend && npm run dev

# Alias for backend (more descriptive)
dev-back: back

# Alias for frontend (more descriptive)
dev-front: front

# Run both backend and frontend
dev:
	@echo "🚀 Starting development servers..."
	@echo "Backend will be available at http://localhost:8000"
	@echo "Frontend will be available at http://localhost:5173"
	@echo ""
	@$(MAKE) -j2 back front

# Docker Compose commands
docker-up:
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "PostgreSQL: localhost:5433"
	@echo "Redis: localhost:6380"

docker-down:
	docker-compose down

docker-clean:
	docker-compose down -v
	@echo "✅ Services stopped and volumes removed"

docker-logs:
	docker-compose logs -f

docker-restart:
	@$(MAKE) docker-down
	@$(MAKE) docker-up

# Database commands (requires PostgreSQL to be running)
db-init:
	@echo "🗄️  Initializing database..."
	psql -h localhost -p 5433 -U postgres -d propertyflow -f database/schema.sql
	psql -h localhost -p 5433 -U postgres -d propertyflow -f database/seed.sql
	@echo "✅ Database initialized!"

db-reset:
	@echo "⚠️  Resetting database..."
	psql -h localhost -p 5433 -U postgres -c "DROP DATABASE IF EXISTS propertyflow;"
	psql -h localhost -p 5433 -U postgres -c "CREATE DATABASE propertyflow;"
	@$(MAKE) db-init

# Linting
lint:
	@echo "🔍 Linting backend..."
	cd backend && uv run ruff check . || true
	@echo "🔍 Linting frontend..."
	cd frontend && npm run lint || true

# Formatting
format:
	@echo "✨ Formatting backend code..."
	cd backend && uv run ruff format . || true
	@echo "✨ Formatting frontend code..."
	cd frontend && npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css}" || true

# Pre-commit hooks (original command kept for compatibility)
pre-commit:
	cd backend && uv add --dev pre-commit
	cd backend && uv run pre-commit install --install-hooks --overwrite
	@echo "✅ Pre-commit hooks installed!"

# Testing
test-back:
	@echo "🧪 Running backend tests..."
	cd backend && uv run pytest

test-front:
	@echo "🧪 Running frontend tests..."
	cd frontend && npm test

test: test-back test-front

# Clean commands
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	cd frontend && rm -rf dist .vite 2>/dev/null || true
	@echo "✅ Clean complete!"

clean-all: clean
	@echo "🧹 Deep cleaning (removing dependencies)..."
	rm -rf backend/.venv
	rm -rf frontend/node_modules
	rm -rf .nix-postgres
	@echo "✅ Deep clean complete! Run 'make install' to reinstall dependencies."

# Build commands
build-front:
	@echo "🏗️  Building frontend..."
	cd frontend && npm run build

build-back:
	@echo "🏗️  Building backend Docker image..."
	cd backend && docker build -t base360-backend .

build: build-back build-front

# Health checks
health:
	@echo "🏥 Checking service health..."
	@curl -sf http://localhost:8000/health || echo "❌ Backend is down"
	@curl -sf http://localhost:3000 || echo "❌ Frontend is down"
	@pg_isready -h localhost -p 5433 || echo "❌ PostgreSQL is down"
	@redis-cli -h localhost -p 6380 ping || echo "❌ Redis is down"

# Show running services
status:
	@echo "📊 Service Status:"
	@echo ""
	@docker-compose ps

# Nix-specific commands
nix-update:
	@echo "📦 Updating Nix flake..."
	nix flake update
	@echo "✅ Flake updated!"

nix-check:
	@echo "🔍 Checking Nix flake..."
	nix flake check

# Development utilities
watch-back:
	@echo "👀 Watching backend for changes..."
	cd backend && uv run watchfiles 'uvicorn app.main:app --reload' app

shell-back:
	@echo "🐚 Entering backend shell..."
	@nix develop .#backend

shell-front:
	@echo "🐚 Entering frontend shell..."
	@nix develop .#frontend

# Quick reset - useful when things go wrong
reset: docker-clean clean
	@echo "♻️  Resetting project..."
	@$(MAKE) setup
	@$(MAKE) docker-up
	@echo "✅ Project reset complete!"
