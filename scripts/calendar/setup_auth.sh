#!/bin/bash

echo "📅 Google Calendar Authentication Setup"
echo "=========================================="
echo

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Using default paths:"
    echo "  GOOGLE_CALENDAR_CREDENTIALS_PATH=credentials/credentials.json"
    echo "  GOOGLE_CALENDAR_TOKEN_PATH=credentials/token.json"
    echo
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if credentials directory exists
if [ ! -d "credentials" ]; then
    echo "📁 Creating credentials directory..."
    mkdir -p credentials
    echo "✅ Directory created"
    echo
fi

# Check if credentials file exists
CREDENTIALS_PATH=${GOOGLE_CALENDAR_CREDENTIALS_PATH:-credentials/credentials.json}
if [ ! -f "$CREDENTIALS_PATH" ]; then
    echo "❌ Credentials file not found: $CREDENTIALS_PATH"
    echo
    echo "📝 Setup instructions:"
    echo "1. Go to https://console.cloud.google.com/"
    echo "2. Create a project (or select existing)"
    echo "3. Enable 'Google Calendar API'"
    echo "4. Go to 'Credentials' → 'Create Credentials' → 'OAuth client ID'"
    echo "5. Choose 'Desktop app' as application type"
    echo "6. Download the JSON file"
    echo "7. Save it as: $CREDENTIALS_PATH"
    echo
    echo "Or set GOOGLE_CALENDAR_CREDENTIALS_PATH in your .env file"
    exit 1
fi

# Install authentication dependencies
echo "📦 Installing authentication dependencies..."
DIR=$(dirname "$0")
cd "$(dirname "$DIR")/.." || exit 1

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    pip install -q google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed successfully"
else
    echo "⚠️  requirements.txt not found, installing minimal dependencies..."
    pip install -q google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv
fi

echo

# Run authentication script
echo "🚀 Starting Google Calendar authentication..."
echo "🌐 A browser window will open for authorization"
echo

python3 "$DIR/auth_calendar.py"

if [ $? -eq 0 ]; then
    echo
    echo "🎉 Authentication completed successfully!"
    echo "You can now run the application with calendar sync enabled"
    echo
    echo "💡 Tip: The token will be automatically refreshed when it expires"
else
    echo
    echo "❌ Authentication failed. Please check your credentials and try again."
    exit 1
fi

