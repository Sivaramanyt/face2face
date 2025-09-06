import os
import asyncio
from pyrogram import Client
from config import Config

async def setup_webhook():
    """Setup webhook for your Koyeb deployment"""
    webhook_url = "https://faint-allegra-rolexsir-7a1ec4b1.koyeb.app/webhook"
    
    app = Client(
        "webhook_setup",
        bot_token=Config.BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH
    )
    
    async with app:
        await app.set_webhook(webhook_url)
        print(f"✅ Webhook set to: {webhook_url}")
        print(f"🤖 Bot is now ready to receive updates!")

if __name__ == "__main__":
    asyncio.run(setup_webhook())
    
