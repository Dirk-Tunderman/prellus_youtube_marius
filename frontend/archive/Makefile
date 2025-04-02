.PHONY: dev prod help clean

# Default target when just typing 'make'
help:
	@echo "Available commands:"
	@echo "  make dev   - Start development server (npm run dev)"
	@echo "  make prod  - Build and run production version locally"
	@echo "  make clean - Remove old containers and images"
	@echo ""
	@echo "After running 'make prod', visit: http://localhost:3000"

# Development server
dev:
	npm run start

# Clean up old containers and images
clean:
	@echo "🧹 Cleaning up old containers and images..."
	-docker stop $$(docker ps -q --filter ancestor=prellus_frontend) 2>/dev/null || true
	-docker rm $$(docker ps -a -q --filter ancestor=prellus_frontend) 2>/dev/null || true
	-docker rmi prellus_frontend 2>/dev/null || true

# Production build and run locally
prod: clean
	@echo "🏗️  Building production version..."
	nixpacks build . --name prellus_frontend
	@echo "\n🚀 Starting production server..."
	@echo "👉 Once running, visit: http://localhost:3000\n"
	docker run -p 3000:3000 prellus_frontend