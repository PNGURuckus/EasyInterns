#!/bin/bash

# EasyInterns Backend Deployment Script for Fly.io
set -e

echo "🚀 Deploying EasyInterns backend to Fly.io..."

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed. Please install it first:"
    echo "curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if user is logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io. Please run: flyctl auth login"
    exit 1
fi

echo "✅ Fly.io CLI check passed"

# Check if app exists, create if not
APP_NAME="easyinterns-api"
if ! flyctl apps list | grep -q "$APP_NAME"; then
    echo "📦 Creating Fly.io app: $APP_NAME"
    flyctl apps create "$APP_NAME" --org personal
else
    echo "✅ App $APP_NAME already exists"
fi

# Set secrets (only if not already set)
echo "🔐 Setting up secrets..."

# Check if secrets exist before setting them
secrets_to_set=()

if ! flyctl secrets list -a "$APP_NAME" | grep -q "SUPABASE_URL"; then
    secrets_to_set+=("SUPABASE_URL")
fi

if ! flyctl secrets list -a "$APP_NAME" | grep -q "SUPABASE_SERVICE_KEY"; then
    secrets_to_set+=("SUPABASE_SERVICE_KEY")
fi

if ! flyctl secrets list -a "$APP_NAME" | grep -q "SUPABASE_JWT_SECRET"; then
    secrets_to_set+=("SUPABASE_JWT_SECRET")
fi

if ! flyctl secrets list -a "$APP_NAME" | grep -q "OPENAI_API_KEY"; then
    secrets_to_set+=("OPENAI_API_KEY")
fi

if ! flyctl secrets list -a "$APP_NAME" | grep -q "SECRET_KEY"; then
    secrets_to_set+=("SECRET_KEY")
fi

if [ ${#secrets_to_set[@]} -gt 0 ]; then
    echo "⚠️ The following secrets need to be set:"
    for secret in "${secrets_to_set[@]}"; do
        echo "  - $secret"
    done
    echo ""
    echo "Please set them using:"
    echo "flyctl secrets set SUPABASE_URL=\"your-url\" SUPABASE_SERVICE_KEY=\"your-key\" -a $APP_NAME"
    echo ""
    read -p "Have you set all required secrets? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Please set the secrets first, then run this script again"
        exit 1
    fi
else
    echo "✅ All required secrets are already set"
fi

# Deploy the application
echo "🚀 Deploying application..."
flyctl deploy -a "$APP_NAME"

# Check deployment status
echo "📊 Checking deployment status..."
flyctl status -a "$APP_NAME"

# Test health endpoint
echo "🏥 Testing health endpoint..."
sleep 10  # Wait for app to start
APP_URL="https://$APP_NAME.fly.dev"
if curl -f "$APP_URL/health" > /dev/null 2>&1; then
    echo "✅ Health check passed!"
    echo "🌐 Backend is live at: $APP_URL"
else
    echo "⚠️ Health check failed. Check logs with: flyctl logs -a $APP_NAME"
fi

echo ""
echo "🎉 Backend deployment complete!"
echo "📊 Monitor with: flyctl dashboard $APP_NAME"
echo "📋 View logs with: flyctl logs -a $APP_NAME"
