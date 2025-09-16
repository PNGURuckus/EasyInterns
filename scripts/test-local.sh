#!/bin/bash

# EasyInterns Local Testing Script
set -e

echo "🧪 Testing EasyInterns application locally..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./scripts/setup-dev.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Copy from .env.example and configure"
    exit 1
fi

echo "✅ Environment setup check passed"

# Test backend
echo "🔧 Testing backend..."

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found"
    exit 1
fi

# Run backend tests
echo "📋 Running backend tests..."
python -m pytest tests/ -v --tb=short

# Start backend in background for integration testing
echo "🚀 Starting backend server..."
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Test health endpoint
echo "🏥 Testing backend health endpoint..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend health check passed"
else
    echo "❌ Backend health check failed"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Test API endpoints
echo "📡 Testing API endpoints..."

# Test internships endpoint
if curl -f http://localhost:8000/api/internships > /dev/null 2>&1; then
    echo "✅ Internships API working"
else
    echo "⚠️ Internships API not responding"
fi

# Stop backend
kill $BACKEND_PID 2>/dev/null || true
echo "🛑 Backend stopped"

# Test frontend if Node.js is available
if command -v node > /dev/null 2>&1; then
    if [ -d "frontend-next" ]; then
        echo "🎨 Testing frontend..."
        cd frontend-next
        
        # Check if dependencies are installed
        if [ ! -d "node_modules" ]; then
            echo "📦 Installing frontend dependencies..."
            npm install
        fi
        
        # Check if .env.local exists
        if [ ! -f ".env.local" ]; then
            echo "⚠️ .env.local not found, creating from template..."
            cp .env.example .env.local
        fi
        
        # Run frontend build test
        echo "🔨 Testing frontend build..."
        npm run build
        
        # Run frontend tests if they exist
        if [ -f "playwright.config.ts" ]; then
            echo "🎭 Running frontend E2E tests..."
            npx playwright test --reporter=line
        fi
        
        echo "✅ Frontend tests completed"
        cd ..
    fi
else
    echo "⚠️ Node.js not found, skipping frontend tests"
fi

echo ""
echo "🎉 Local testing completed successfully!"
echo ""
echo "To run the application locally:"
echo "1. Backend: python main.py"
echo "2. Frontend: cd frontend-next && npm run dev"
echo ""
echo "Access the application at:"
echo "- Backend API: http://localhost:8000"
echo "- Frontend: http://localhost:3000"
