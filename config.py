import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram Bot Config
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH")
    
    # Face2Face Config
    GPU_DEVICE = int(os.getenv("GPU_DEVICE", "-1"))
    ENHANCE_MODEL = os.getenv("ENHANCE_MODEL", "gpen_bfr_512")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "50")) * 1024 * 1024  # MB to bytes
    
    # Deployment Config
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    PORT = int(os.getenv("PORT", "8000"))
    
    # Validate required variables
    @classmethod
    def validate(cls):
        required = ["BOT_TOKEN", "API_ID", "API_HASH"]
        missing = [var for var in required if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")

# Validate config on import
Config.validate()
