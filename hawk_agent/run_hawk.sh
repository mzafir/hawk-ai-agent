#!/bin/bash

echo "🦅 Hawk Agent - Project Status Monitor"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check credentials
echo "🔑 Checking credentials..."
if [ ! -f "credentials.json" ]; then
    echo "❌ credentials.json not found"
    echo "Running setup script..."
    python setup_credentials.py
    echo ""
    echo "Please complete the Google API setup and run this script again."
    exit 1
fi

# Check environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your settings"
fi

echo "✅ Setup complete!"
echo ""
echo "🚀 Starting Hawk Agent..."
python hawk_agent.py