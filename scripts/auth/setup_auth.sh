#!/bin/bash

echo "🔐 Telegram Authentication Setup"
echo "=========================================="
echo

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create a .env file with your Telegram credentials:"
    echo "  TELEGRAM_API_ID=your_api_id"
    echo "  TELEGRAM_API_HASH=your_api_hash"
    echo "  TELEGRAM_PHONE_NUMBER=your_phone_number"
    echo
    echo "You can get these from https://my.telegram.org/"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Install authentication dependencies
echo "📦 Installing authentication dependencies..."
DIR=$(dirname "$0")
pip install -r $DIR/requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"
echo

# Run authentication script
echo "🚀 Starting Telegram authentication..."
echo "📲 Check your Telegram app for the confirmation code!"
echo

python $DIR/auth_telegram.py

if [ $? -eq 0 ]; then
    echo
    echo "🎉 Authentication completed successfully!"
    echo "You can now run: docker-compose up -d"
else
    echo
    echo "❌ Authentication failed. Please check your credentials and try again."
    exit 1
fi
