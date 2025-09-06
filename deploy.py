import os
import asyncio
from pyrogram import Client
from config import Config

async def setup_webhook():
    """Setup webhook for deployment"""
    if Config.WEBHOOK_URL:
        app = Client(
            "webhook_setup",
            bot_token=Config.BOT_TOKEN,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH
        )
        
        async with app:
            await app.set_webhook(Config.WEBHOOK_URL)
            print(f"✅ Webhook set to: {Config.WEBHOOK_URL}")

if __name__ == "__main__":
    asyncio.run(setup_webhook())
