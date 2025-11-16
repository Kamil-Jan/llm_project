import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pyrogram import Client

# Load environment variables
load_dotenv()

def main():
    """Interactive Telegram authentication."""
    print("🔐 Telegram Authentication")
    print("=" * 40)

    # Get credentials from environment
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone_number = os.getenv('TELEGRAM_PHONE_NUMBER')

    if not all([api_id, api_hash, phone_number]):
        print("❌ Missing required environment variables:")
        print("   - TELEGRAM_API_ID")
        print("   - TELEGRAM_API_HASH")
        print("   - TELEGRAM_PHONE_NUMBER")
        print("\nPlease check your .env file.")
        return 1

    # Create sessions directory with proper permissions
    sessions_dir = Path("sessions")
    sessions_dir.mkdir(exist_ok=True)

    # Ensure proper permissions
    try:
        os.chmod(sessions_dir, 0o755)
    except Exception as e:
        print(f"⚠️  Warning: Could not set directory permissions: {e}")

    session_name = "project_userbot"
    session_path = sessions_dir / session_name

    print(f"📱 Phone: {phone_number}")
    print(f"🆔 API ID: {api_id}")
    print(f"💾 Session: {session_path}")
    print()

    try:
        # Create client with explicit session string
        client = Client(
            name=session_name,  # Use just the name, not full path
            api_id=int(api_id),
            api_hash=api_hash,
            phone_number=phone_number,
            workdir=str(sessions_dir.absolute())  # Use absolute path
        )

        print("🚀 Starting authentication...")
        print("📲 Check your Telegram app for the confirmation code!")
        print()

        # Start the client (this will prompt for code if needed)
        with client:
            me = client.get_me()
            print(f"✅ Successfully authenticated as: {me.first_name} (@{me.username})")
            print(f"🆔 User ID: {me.id}")
            print()
            print("💾 Session file saved successfully!")
            print(f"📁 Location: {session_path}.session")
            print()
            print("🎉 You can now run the Docker container!")

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure your API credentials are correct")
        print("2. Check that your phone number is in international format (+1234567890)")
        print("3. Try running: chmod 755 sessions/")
        print("4. Make sure you have write permissions in the current directory")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
