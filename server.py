from flask import Flask, request
import asyncio
import threading
from bot import app as telegram_app
from config import Config

flask_app = Flask(__name__)

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """Handle webhook updates"""
    json_data = request.get_json()
    # Process update (implementation depends on deployment method)
    return "OK"

@flask_app.route('/health')
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "bot": "face_swap_bot"}

def run_telegram_bot():
    """Run Telegram bot in separate thread"""
    telegram_app.run()

if __name__ == "__main__":
    # Start Telegram bot in background
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start Flask server
    flask_app.run(
        host="0.0.0.0", 
        port=Config.PORT,
        debug=False
    )
