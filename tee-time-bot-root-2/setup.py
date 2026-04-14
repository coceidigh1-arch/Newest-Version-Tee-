"""
Setup Helper
Run this locally to configure your Tee Time Bot instance.
Usage: python setup.py
"""

import asyncio
import httpx
import sys
from cryptography.fernet import Fernet


def generate_encryption_key():
    key = Fernet.generate_key().decode()
    print(f"\n🔑 Your encryption key:\n{key}")
    print("\nSet this as ENCRYPTION_KEY in your Railway environment variables.")
    return key


async def setup_telegram_webhook(bot_token: str, app_url: str):
    """Register the Telegram webhook with your deployed app."""
    webhook_url = f"{app_url.rstrip('/')}/telegram/webhook"

    async with httpx.AsyncClient() as client:
        # Set webhook
        response = await client.post(
            f"https://api.telegram.org/bot{bot_token}/setWebhook",
            json={"url": webhook_url, "allowed_updates": ["message"]},
        )
        result = response.json()

        if result.get("ok"):
            print(f"\n✅ Telegram webhook set to: {webhook_url}")
        else:
            print(f"\n❌ Webhook setup failed: {result}")
            return

        # Get bot info
        info = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
        bot = info.json().get("result", {})
        print(f"🤖 Bot name: @{bot.get('username', '?')}")
        print(f"\nTell your friends to message @{bot.get('username', '?')} and type /start")


async def create_admin_user(app_url: str, name: str, telegram_chat_id: str):
    """Create the admin user via the API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{app_url.rstrip('/')}/users",
            json={
                "name": name,
                "telegram_chat_id": telegram_chat_id,
                "is_admin": True,
            },
        )
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Admin user created: {data['id']}")
            print(f"   Name: {name}")
            print(f"   Set preferences: PUT {app_url}/users/{data['id']}/preferences")
            return data["id"]
        else:
            print(f"\n❌ Failed: {response.text}")
            return None


async def set_default_preferences(app_url: str, user_id: str):
    """Set the default Chicago golfer preferences."""
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{app_url.rstrip('/')}/users/{user_id}/preferences",
            json={
                "players": 4,
                "preferred_days": ["saturday", "sunday"],
                "earliest_time": "05:00",
                "latest_time": "08:00",
                "max_price": 150,
                "walk_ride": "ride",
                "max_rounds_week": 2,
                "monthly_budget": 600,
                "must_play_courses": [
                    "bolingbrook", "mistwood", "preserve_oak",
                    "highlands_elgin", "thunderhawk", "schaumburg",
                ],
                "nice_to_have_courses": [
                    "cantigny", "cog_hill_123", "harborside",
                    "prairie_landing", "bowes_creek",
                ],
                "deal_only_courses": [
                    "stonewall", "sanctuary", "glen_club", "cog_hill_4",
                ],
                "alert_threshold": 55,
                "confirm_threshold": 75,
                "autobook_threshold": 90,
            },
        )
        if response.status_code == 200:
            print("✅ Default preferences set (Sat/Sun before 8am, 4 players)")
        else:
            print(f"❌ Failed: {response.text}")


def main():
    print("=" * 50)
    print("⛳ Tee Time Bot Setup")
    print("=" * 50)

    print("\nWhat would you like to do?")
    print("1. Generate encryption key")
    print("2. Set up Telegram webhook")
    print("3. Create admin user")
    print("4. Full setup (all of the above)")
    print("5. Exit")

    choice = input("\nChoice (1-5): ").strip()

    if choice == "1":
        generate_encryption_key()

    elif choice == "2":
        token = input("Telegram bot token: ").strip()
        url = input("Your Railway app URL (e.g., https://tee-time-bot.up.railway.app): ").strip()
        asyncio.run(setup_telegram_webhook(token, url))

    elif choice == "3":
        url = input("Your Railway app URL: ").strip()
        name = input("Your name: ").strip()
        chat_id = input("Your Telegram chat ID (message the bot /start to get it): ").strip()
        user_id = asyncio.run(create_admin_user(url, name, chat_id))
        if user_id:
            asyncio.run(set_default_preferences(url, user_id))

    elif choice == "4":
        # Full setup
        print("\n--- Step 1: Encryption Key ---")
        key = generate_encryption_key()

        print("\n--- Step 2: Telegram Webhook ---")
        token = input("\nTelegram bot token: ").strip()
        url = input("Your Railway app URL: ").strip()
        asyncio.run(setup_telegram_webhook(token, url))

        print("\n--- Step 3: Admin User ---")
        name = input("\nYour name: ").strip()
        chat_id = input("Your Telegram chat ID: ").strip()
        user_id = asyncio.run(create_admin_user(url, name, chat_id))
        if user_id:
            asyncio.run(set_default_preferences(url, user_id))

        print("\n" + "=" * 50)
        print("✅ Setup complete!")
        print("=" * 50)
        print(f"\n📱 Dashboard: {url}/docs")
        print(f"🔍 Health: {url}/health")
        print(f"⛳ Courses: {url}/courses")
        print(f"\nThe bot is now scanning every 10 minutes.")
        print(f"You'll receive Telegram alerts when matching tee times appear.")

    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
