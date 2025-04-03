.PHONY: start stop restart status logs kill-ports clean-start help

# Configuration
FRONTEND_DIR = frontend
BACKEND_DIR = app
VENV_DIR = $(BACKEND_DIR)/.venv
PID_DIR = .pid
LOGS_DIR = logs
FRONTEND_PORT = 5173
BACKEND_PORT = 5001

# Default target
help:
	@echo "Available commands:"
	@echo "  make start       - Start both frontend and backend"
	@echo "  make stop        - Stop all running services"
	@echo "  make restart     - Restart all services"
	@echo "  make status      - Check status of services"
	@echo "  make logs        - View logs (usage: make logs SERVICE=frontend|backend)"
	@echo "  make kill-ports  - Kill processes using ports $(FRONTEND_PORT) and $(BACKEND_PORT)"
	@echo "  make clean-start - Stop services, kill port processes, and start fresh"

# Kill ports command
kill-ports:
	@echo "Checking for processes using ports $(FRONTEND_PORT) and $(BACKEND_PORT)..."
	@# Kill process using frontend port (if any)
	@lsof -ti:$(FRONTEND_PORT) > /dev/null 2>&1 && \
		echo "Killing process on port $(FRONTEND_PORT)..." && \
		lsof -ti:$(FRONTEND_PORT) | xargs kill -9 || \
		echo "No process found on port $(FRONTEND_PORT)"
	@# Kill process using backend port (if any)
	@lsof -ti:$(BACKEND_PORT) > /dev/null 2>&1 && \
		echo "Killing process on port $(BACKEND_PORT)..." && \
		lsof -ti:$(BACKEND_PORT) | xargs kill -9 || \
		echo "No process found on port $(BACKEND_PORT)"
	@echo "Ports are now free."

# Start command
start: kill-ports
	@mkdir -p $(PID_DIR)
	@mkdir -p $(LOGS_DIR)
	@echo "Starting frontend..."
	@(cd $(FRONTEND_DIR) && npm run dev > $(PWD)/$(LOGS_DIR)/frontend.log 2>&1 & echo $$! > $(PWD)/$(PID_DIR)/frontend.pid)
	@echo "Starting backend..."
	@if [ ! -d "$(BACKEND_DIR)/.venv" ]; then \
		echo "Error: Virtual environment not found at $(BACKEND_DIR)/.venv"; \
		echo "Please create it first with: cd $(BACKEND_DIR) && python -m venv .venv"; \
		exit 1; \
	fi
	@(cd $(BACKEND_DIR) && source .venv/bin/activate && python main.py > $(PWD)/$(LOGS_DIR)/backend.log 2>&1 & echo $$! > $(PWD)/$(PID_DIR)/backend.pid)
	@echo "All services started. Use 'make status' to check status."
	@echo "View logs with: make logs SERVICE=frontend|backend"

# Stop command
stop:
	@echo "Stopping services..."
	@if [ -f $(PID_DIR)/frontend.pid ]; then \
		echo "Stopping frontend (PID: `cat $(PID_DIR)/frontend.pid`)..."; \
		kill -15 `cat $(PID_DIR)/frontend.pid` 2>/dev/null && rm $(PID_DIR)/frontend.pid; \
	else \
		echo "Frontend is not running"; \
	fi
	@if [ -f $(PID_DIR)/backend.pid ]; then \
		echo "Stopping backend (PID: `cat $(PID_DIR)/backend.pid`)..."; \
		kill -15 `cat $(PID_DIR)/backend.pid` 2>/dev/null && rm $(PID_DIR)/backend.pid; \
	else \
		echo "Backend is not running"; \
	fi
	@echo "All services stopped."

# Clean start command
clean-start: stop kill-ports
	@sleep 2
	@$(MAKE) start

# Restart command
restart: stop
	@sleep 2
	@$(MAKE) start

# Status command
status:
	@echo "=== Application Status ==="
	@if [ -f $(PID_DIR)/frontend.pid ] && kill -0 `cat $(PID_DIR)/frontend.pid` 2>/dev/null; then \
		echo "Frontend: Running (PID: `cat $(PID_DIR)/frontend.pid`)"; \
	else \
		echo "Frontend: Stopped"; \
	fi
	@if [ -f $(PID_DIR)/backend.pid ] && kill -0 `cat $(PID_DIR)/backend.pid` 2>/dev/null; then \
		echo "Backend: Running (PID: `cat $(PID_DIR)/backend.pid`)"; \
	else \
		echo "Backend: Stopped"; \
	fi
	@echo "========================="

# Logs command
logs:
	@if [ "$(SERVICE)" = "frontend" ]; then \
		if [ -f $(LOGS_DIR)/frontend.log ]; then \
			tail -f $(LOGS_DIR)/frontend.log; \
		else \
			echo "Frontend log file not found"; \
		fi; \
	elif [ "$(SERVICE)" = "backend" ]; then \
		if [ -f $(LOGS_DIR)/backend.log ]; then \
			tail -f $(LOGS_DIR)/backend.log; \
		else \
			echo "Backend log file not found"; \
		fi; \
	else \
		echo "Usage: make logs SERVICE=frontend|backend"; \
	fi
