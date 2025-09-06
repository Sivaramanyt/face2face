import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram Bot Config (Your Values)
    BOT_TOKEN = "8261755198:AAFikWiiAzIuRN_p8UmAtWslhhy18ia2TBg"
    API_ID = 29542645
    API_HASH = "06e505b8418565356ae79365df5d69e0"
    
    # Face2Face Config
    GPU_DEVICE = int(os.getenv("GPU_DEVICE", "-1"))
    ENHANCE_MODEL = os.getenv("ENHANCE_MODEL", "gpen_bfr_512")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "50")) * 1024 * 1024  # MB to bytes
    
    # Deployment Config (Your Koyeb URL)
    WEBHOOK_URL = "https://faint-allegra-rolexsir-7a1ec4b1.koyeb.app/webhook"
    PORT = int(os.getenv("PORT", "8080"))
    
    # Validate required variables
    @classmethod
    def validate(cls):
        required = ["BOT_TOKEN", "API_ID", "API_HASH"]
        missing = [var for var in required if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")

# Validate config on import
Config.validate()
        
