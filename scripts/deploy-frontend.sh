#!/bin/bash

# EasyInterns Frontend Deployment Script for Vercel
set -e

echo "🚀 Deploying EasyInterns frontend to Vercel..."

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    if [ -d "frontend-next" ]; then
        echo "📁 Changing to frontend directory..."
        cd frontend-next
    else
        echo "❌ Frontend directory not found"
        exit 1
    fi
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm"
    exit 1
fi

echo "✅ Node.js and npm check passed"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    if [ -f ".env.example" ]; then
        echo "⚙️ Creating .env.local from template..."
        cp .env.example .env.local
        echo "📝 Please edit .env.local with your actual configuration values"
        echo "Required variables:"
        echo "  - NEXT_PUBLIC_SUPABASE_URL"
        echo "  - NEXT_PUBLIC_SUPABASE_ANON_KEY"
        echo "  - NEXT_PUBLIC_API_URL"
        echo ""
        read -p "Have you configured .env.local? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Please configure .env.local first"
            exit 1
        fi
    else
        echo "❌ No .env.example found. Please create .env.local manually"
        exit 1
    fi
fi

# Build the application
echo "🔨 Building application..."
npm run build

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# Check if user is logged in to Vercel
if ! vercel whoami &> /dev/null; then
    echo "🔐 Please log in to Vercel..."
    vercel login
fi

echo "✅ Vercel CLI check passed"

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
vercel --prod

# Get deployment URL
DEPLOYMENT_URL=$(vercel ls --scope $(vercel whoami) | grep easyinterns | head -1 | awk '{print $2}')

if [ -n "$DEPLOYMENT_URL" ]; then
    echo ""
    echo "🎉 Frontend deployment complete!"
    echo "🌐 Frontend is live at: https://$DEPLOYMENT_URL"
    echo "📊 Manage at: https://vercel.com/dashboard"
else
    echo "⚠️ Could not determine deployment URL. Check Vercel dashboard."
fi

echo ""
echo "Next steps:"
echo "1. Verify the deployment works correctly"
echo "2. Set up custom domain (optional)"
echo "3. Configure environment variables in Vercel dashboard if needed"
