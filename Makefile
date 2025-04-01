.PHONY: dev prod help clean build-all run-all stop-all

# Container names
FRONTEND_NAME = prellus_frontend
BACKEND_NAME = prellus_backend

# Default target
help:
	@echo "Available commands:"
	@echo "  make build-all  - Build both frontend and backend containers"
	@echo "  make run-all    - Run both containers with Docker Compose"
	@echo "  make stop-all   - Stop all containers"
	@echo "  make clean      - Remove all containers and images"
	@echo "  make dev        - Run both services in development mode"
	@echo ""
	@echo "Individual service commands:"
	@echo "  make frontend-build  - Build frontend container"
	@echo "  make backend-build   - Build backend container"
	@echo "  make logs           - View Docker Compose logs"

# Build commands
frontend-build:
	@echo "🏗️  Building frontend..."
	cd frontend && nixpacks build . --name $(FRONTEND_NAME)

backend-build:
	@echo "🏗️  Building backend..."
	cd backend && nixpacks build . --name $(BACKEND_NAME)

build-all: frontend-build backend-build

# Run commands
run-all:
	@echo "🚀 Starting services with Docker Compose..."
	docker compose up -d
	@echo "✨ All services are starting up..."
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8000"

# View logs
logs:
	docker compose logs -f

# Stop commands
stop-all:
	@echo "🛑 Stopping all containers..."
	docker compose down

# Clean up
clean: stop-all
	@echo "🧹 Cleaning up containers and images..."
	-docker rmi $(FRONTEND_NAME) 2>/dev/null || true
	-docker rmi $(BACKEND_NAME) 2>/dev/null || true

# Development mode (if needed)
dev:
	@echo "Starting development servers..."
	cd frontend && npm run dev & \
	cd backend && python -m uvicorn main:app --reload --port 8000 