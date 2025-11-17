import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Load environment variables
load_dotenv()

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']


def main():
    """Interactive Google Calendar authentication."""
    print("📅 Google Calendar Authentication")
    print("=" * 40)

    # Get credentials path from environment
    credentials_path = os.getenv('GOOGLE_CALENDAR_CREDENTIALS_PATH', 'credentials/credentials.json')
    token_path = os.getenv('GOOGLE_CALENDAR_TOKEN_PATH', 'credentials/token.json')

    # Convert to Path objects
    credentials_file = Path(credentials_path)
    token_file = Path(token_path)

    # Check if credentials file exists
    if not credentials_file.exists():
        print(f"❌ Credentials file not found: {credentials_file}")
        print("\n📝 Setup instructions:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a project and enable Google Calendar API")
        print("3. Create OAuth 2.0 credentials (Desktop app)")
        print(f"4. Download and save as: {credentials_file}")
        print("\nOr set GOOGLE_CALENDAR_CREDENTIALS_PATH in your .env file")
        return 1

    # Create token directory if it doesn't exist
    token_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"📁 Credentials: {credentials_file.absolute()}")
    print(f"💾 Token will be saved to: {token_file.absolute()}")
    print()

    try:
        # Create OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_file.absolute()),
            SCOPES
        )

        print("🚀 Starting authentication...")
        print("🌐 A browser window will open for authorization")
        print("📋 Please authorize the application to access your Google Calendar")
        print()

        # Run the OAuth flow
        creds = flow.run_local_server(port=0)

        # Save the token
        print(f"💾 Saving token to {token_file.absolute()}...")
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

        print()
        print("✅ Successfully authenticated with Google Calendar!")
        print(f"💾 Token saved to: {token_file.absolute()}")
        print()
        print("🎉 You can now run the application with calendar sync enabled!")

    except FileNotFoundError:
        print(f"❌ Credentials file not found: {credentials_file}")
        print("Please download your OAuth credentials from Google Cloud Console")
        return 1
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure your credentials.json file is valid")
        print("2. Check that Google Calendar API is enabled in your project")
        print("3. Verify the OAuth consent screen is configured")
        print("4. Make sure you have write permissions for the token directory")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

