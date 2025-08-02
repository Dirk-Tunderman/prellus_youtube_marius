#!/bin/bash

# YouTube Transcript Processor - Startup Script
# This script starts both frontend and backend services

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_DIR="$SCRIPT_DIR/app"
VENV_DIR="$BACKEND_DIR/.venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[STARTUP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        print_warning "Killing existing processes on port $port"
        echo $pids | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    print_status "Waiting for $service_name to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi

        if [ $((attempt % 5)) -eq 0 ]; then
            print_status "Still waiting for $service_name... (attempt $attempt/$max_attempts)"
        fi

        sleep 1
        attempt=$((attempt + 1))
    done

    print_error "$service_name failed to start within $max_attempts seconds"
    return 1
}

# Cleanup function
cleanup() {
    print_warning "Shutting down services..."
    kill_port 5001  # Backend
    kill_port 5173  # Frontend (Vite default)
    kill_port 5174  # Frontend (alternative)
    kill_port 5175  # Frontend (alternative)
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

print_status "🚀 Starting YouTube Transcript Processor..."
echo "======================================================="

# Check if directories exist
if [ ! -d "$FRONTEND_DIR" ]; then
    print_error "Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

if [ ! -d "$BACKEND_DIR" ]; then
    print_error "Backend directory not found: $BACKEND_DIR"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    print_error "Python virtual environment not found: $VENV_DIR"
    print_status "Creating virtual environment..."
    cd "$BACKEND_DIR"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cd "$SCRIPT_DIR"
    print_success "Virtual environment created and dependencies installed"
fi

# Check if node_modules exists
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    print_error "Node modules not found in frontend directory"
    print_status "Installing frontend dependencies..."
    cd "$FRONTEND_DIR"
    npm install
    cd "$SCRIPT_DIR"
    print_success "Frontend dependencies installed"
fi

# Kill any existing processes on our ports
kill_port 5001
kill_port 5173
kill_port 5174
kill_port 5175

print_status "Starting backend server..."
cd "$BACKEND_DIR"
source .venv/bin/activate
nohup python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

print_status "Starting frontend development server..."
cd "$FRONTEND_DIR"
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

# Wait for services to be ready
if wait_for_service "http://localhost:5001/api/test" "Backend API"; then
    print_success "✅ Backend running on http://localhost:5001"
else
    print_error "❌ Backend failed to start"
    cleanup
    exit 1
fi

# Wait a bit for frontend to start
sleep 3

# Check for frontend on common ports
FRONTEND_URL=""
for port in 5173 5174 5175; do
    if check_port $port; then
        FRONTEND_URL="http://localhost:$port"
        break
    fi
done

if [ ! -z "$FRONTEND_URL" ]; then
    print_success "✅ Frontend running on $FRONTEND_URL"
else
    print_warning "⚠️  Frontend may still be starting up..."
    FRONTEND_URL="http://localhost:5173"
fi

echo "======================================================="
print_success "🎉 Application started successfully!"
echo ""
echo "📱 Frontend: $FRONTEND_URL"
echo "🔧 Backend API: http://localhost:5001"
echo "🩺 Health Check: http://localhost:5001/api/test"
echo ""
echo "📋 Logs:"
echo "   Backend: logs/backend.log"
echo "   Frontend: logs/frontend.log"
echo ""
echo "🛑 To stop: Press Ctrl+C or run 'make stop'"
echo "======================================================="

# Keep script running and monitor processes
while true; do
    # Check if backend is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend process died unexpectedly"
        cleanup
        exit 1
    fi

    # Check if frontend is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "Frontend process died unexpectedly"
        cleanup
        exit 1
    fi

    sleep 5
done
