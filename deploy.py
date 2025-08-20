#!/usr/bin/env python3
"""
Deployment helper script for the Supper Bot
Run this after deploying to set up the webhook
"""

import asyncio
import os
from src.tgbot.infrastructure.bot import bot
from src.tgbot.infrastructure.config import settings

async def setup_webhook():
    """Set up the webhook for the bot."""
    try:
        # Get the webhook URL from environment
        webhook_url = os.environ.get("WEBHOOK_URL")
        if not webhook_url:
            print("❌ WEBHOOK_URL environment variable not set!")
            print("Please set it to your deployed app URL + /{secret_token}")
            return
        
        print(f"🔗 Setting webhook to: {webhook_url}")
        
        # Remove any existing webhook
        await bot.remove_webhook()
        
        # Set the new webhook
        result = await bot.set_webhook(url=webhook_url)
        
        if result:
            print("✅ Webhook set successfully!")
            
            # Get webhook info
            webhook_info = await bot.get_webhook_info()
            print(f"📡 Webhook URL: {webhook_info.url}")
            print(f"📊 Pending updates: {webhook_info.pending_update_count}")
        else:
            print("❌ Failed to set webhook")
            
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
    
    finally:
        await bot.close_session()

if __name__ == "__main__":
    print("🚀 Setting up webhook for Supper Bot...")
    asyncio.run(setup_webhook())
