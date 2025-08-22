#!/bin/bash

# FLAC Music Store - One-Click Setup and Run Script
# This script sets up dependencies and runs the entire application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_status "Starting FLAC Music Store setup..."
print_status "Working directory: $SCRIPT_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed. Please install Python3 first."
    exit 1
fi

print_success "Python3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip3 first."
    exit 1
fi

print_success "pip3 found"

# Navigate to backend directory
cd backend

# Check if virtual environment exists and is properly set up
VENV_AVAILABLE=true
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    print_status "Creating Python virtual environment..."
    rm -rf venv  # Remove incomplete venv if it exists
    
    # Try to create virtual environment
    if python3 -m venv venv 2>/dev/null; then
        print_success "Virtual environment created"
    else
        print_warning "Could not create virtual environment (python3-venv may not be installed)"
        print_warning "Continuing without virtual environment..."
        VENV_AVAILABLE=false
    fi
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment if available
if [ "$VENV_AVAILABLE" = true ] && [ -f "venv/bin/activate" ]; then
    print_status "Activating virtual environment..."
    source venv/bin/activate
else
    print_status "Running without virtual environment (using system Python)"
fi

# Check if requirements are already installed
print_status "Checking dependencies..."
REQUIREMENTS_FILE="requirements.txt"

# Function to check if a package is installed
check_package() {
    python3 -c "import $1" 2>/dev/null
}

# Install requirements if not already installed
INSTALL_NEEDED=false

# Read requirements and check each package
while IFS= read -r line; do
    if [[ ! -z "$line" && ! "$line" =~ ^#.* ]]; then
        # Extract package name (before any version specifiers)
        PACKAGE=$(echo "$line" | sed 's/[>=<].*//' | tr '-' '_')
        if ! check_package "$PACKAGE" 2>/dev/null; then
            INSTALL_NEEDED=true
            break
        fi
    fi
done < "$REQUIREMENTS_FILE"

if [ "$INSTALL_NEEDED" = true ]; then
    print_status "Installing Python dependencies..."
    
    # Try to install with pip, handling different scenarios
    if [ "$VENV_AVAILABLE" = true ]; then
        # In virtual environment, normal pip install should work
        if pip3 install -r requirements.txt; then
            print_success "Dependencies installed successfully"
        else
            print_error "Failed to install dependencies in virtual environment"
            exit 1
        fi
    else
        # Not in venv, need to handle externally-managed environment
        print_warning "Virtual environment not available. Attempting to install system-wide..."
        
        if pip3 install -r requirements.txt --break-system-packages; then
            print_warning "Dependencies installed with --break-system-packages flag"
            print_success "Dependencies installed successfully"
        else
            print_error "Failed to install dependencies. To fix this, please run:"
            print_error ""
            print_error "  sudo apt update"
            print_error "  sudo apt install python3.12-venv python3-pip"
            print_error ""
            print_error "Then re-run this script."
            print_error ""
            print_error "Alternative: Install dependencies manually with:"
            print_error "  pip3 install -r backend/requirements.txt --break-system-packages"
            exit 1
        fi
    fi
else
    print_status "All dependencies are already installed"
fi

# Create temp directory for downloads if it doesn't exist
if [ ! -d "temp_downloads" ]; then
    mkdir -p temp_downloads
    print_status "Created temp_downloads directory"
fi

# Function to find available port
find_available_port() {
    local port=$1
    while lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; do
        port=$((port + 1))
    done
    echo $port
}

# Find available ports
BACKEND_PORT=$(find_available_port 5000)
FRONTEND_PORT=$(find_available_port 8000)

# Check if backend is already running
if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port $BACKEND_PORT is already in use. Finding alternative..."
    BACKEND_PORT=$(find_available_port $((BACKEND_PORT + 1)))
fi

print_status "Backend will run on port: $BACKEND_PORT"
print_status "Frontend will run on port: $FRONTEND_PORT"

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down services..."
    # Kill background processes
    jobs -p | xargs -r kill
    print_success "Cleanup complete"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Start the Flask backend in the background
print_status "Starting Flask backend..."
export FLASK_APP=app.py
export FLASK_ENV=development

# Start Flask with custom port
python3 app.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ! ps -p $BACKEND_PID > /dev/null; then
    print_error "Failed to start backend"
    exit 1
fi

print_success "Backend started successfully (PID: $BACKEND_PID)"

# Navigate back to project root for frontend
cd "$SCRIPT_DIR"

# Start frontend server
print_status "Starting frontend server..."
cd frontend

# Use Python's built-in HTTP server for frontend
python3 -m http.server $FRONTEND_PORT &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 2

# Check if frontend started successfully
if ! ps -p $FRONTEND_PID > /dev/null; then
    print_error "Failed to start frontend"
    exit 1
fi

print_success "Frontend started successfully (PID: $FRONTEND_PID)"

# Display startup information
echo ""
echo "================================================"
print_success "FLAC Music Store is now running!"
echo "================================================"
echo ""
print_status "🎵 Frontend: http://localhost:$FRONTEND_PORT"
print_status "🔧 Backend API: http://localhost:5000"
print_status "🧪 API Test: http://localhost:5000/api/test"
echo ""
print_status "Press Ctrl+C to stop all services"
echo ""

# Keep the script running and wait for user interruption
wait 