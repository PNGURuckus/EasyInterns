#!/bin/bash

# EasyInterns Comprehensive Test Runner
set -e

echo "🧪 Running comprehensive test suite for EasyInterns..."

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run ./scripts/setup-dev.sh first"
    exit 1
fi

# Backend Tests
echo "🔧 Running backend tests..."

# Unit tests
echo "📋 Running unit tests..."
python -m pytest tests/test_models.py -v --tb=short

# API tests
echo "📡 Running API tests..."
python -m pytest tests/test_api.py -v --tb=short

# Scraper tests
echo "🕷️ Running scraper tests..."
python -m pytest tests/test_scrapers.py -v --tb=short

# Coverage report
echo "📊 Generating coverage report..."
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# Frontend Tests (if Node.js available)
if command -v node > /dev/null 2>&1 && [ -d "frontend-next" ]; then
    echo "🎨 Running frontend tests..."
    cd frontend-next
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    
    # TypeScript check
    echo "🔍 Running TypeScript check..."
    npx tsc --noEmit
    
    # Linting
    echo "🧹 Running ESLint..."
    npm run lint
    
    # E2E tests
    if [ -f "playwright.config.ts" ]; then
        echo "🎭 Running E2E tests..."
        npx playwright test --reporter=line
    fi
    
    cd ..
else
    echo "⚠️ Skipping frontend tests (Node.js not available or frontend not found)"
fi

echo ""
echo "🎉 All tests completed!"
echo "📊 Check htmlcov/index.html for detailed coverage report"
