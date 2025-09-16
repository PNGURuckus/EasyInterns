#!/bin/bash

# EasyInterns Development Setup Script
set -e

echo "🚀 Setting up EasyInterns development environment..."

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
playwright install chromium
playwright install-deps chromium

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your actual configuration values"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs temp

# Check if Node.js is installed for frontend
if command -v node > /dev/null 2>&1; then
    echo "✅ Node.js found"
    
    # Setup frontend
    if [ -d "frontend-next" ]; then
        echo "🎨 Setting up frontend..."
        cd frontend-next
        
        # Install dependencies
        npm install
        
        # Create frontend .env file
        if [ ! -f ".env.local" ]; then
            cp .env.example .env.local
            echo "📝 Please edit frontend-next/.env.local with your configuration"
        fi
        
        cd ..
    fi
else
    echo "⚠️ Node.js not found. Please install Node.js 18+ to run the frontend"
fi

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your actual configuration values"
echo "2. Edit frontend-next/.env.local with your frontend configuration"
echo "3. Start the backend: python main.py"
echo "4. Start the frontend: cd frontend-next && npm run dev"
echo ""
echo "📖 See deploy.md for full deployment instructions"
