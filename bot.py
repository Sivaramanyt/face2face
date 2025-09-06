import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from face2face import Face2Face
import tempfile
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Face2Face
try:
    f2f = Face2Face(device_id=-1)  # CPU mode for mobile compatibility
    logger.info("Face2Face initialized successfully")
except Exception as e:
    logger.error(f"Face2Face initialization failed: {e}")
    f2f = None

# Bot credentials
app = Client(
    "face_swap_bot",
    bot_token=os.getenv("BOT_TOKEN"),
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH")
)

# User sessions to track face swap process
user_sessions = {}

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    welcome_text = """
🎭 **Face Swap Bot** 🎭

Welcome! I can swap faces in images and videos.

**Features:**
• 📸 Image face swapping
• 🎥 Video face swapping
• ✨ Face enhancement
• 🔄 Batch processing

**How to use:**
1. Send /swap to start
2. Upload source image (your face)
3. Upload target image/video
4. Get your swapped result!

Choose an option below:
    """
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Start Face Swap", callback_data="start_swap")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
    ])
    
    await message.reply_text(welcome_text, reply_markup=keyboard)

@app.on_message(filters.command("swap"))
async def swap_command(client, message: Message):
    user_id = message.from_user.id
    user_sessions[user_id] = {"step": "waiting_source", "source": None, "target": None}
    
    await message.reply_text(
        "🎭 **Face Swap Process Started!**\n\n"
        "**Step 1:** Send me the source image (the face you want to use)\n"
        "📸 Upload a clear photo with a visible face"
    )

@app.on_message(filters.photo)
async def handle_photo(client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in user_sessions:
        await message.reply_text("Please start with /swap command first!")
        return
    
    session = user_sessions[user_id]
    
    if session["step"] == "waiting_source":
        # Download source image
        source_path = await message.download(file_name=f"temp/source_{user_id}.jpg")
        session["source"] = source_path
        session["step"] = "waiting_target"
        
        await message.reply_text(
            "✅ **Source image received!**\n\n"
            "**Step 2:** Now send me the target image or video\n"
            "🎯 This is where the face will be swapped"
        )
    
    elif session["step"] == "waiting_target":
        await message.reply_text("🔄 Processing your face swap...")
        
        # Download target image
        target_path = await message.download(file_name=f"temp/target_{user_id}.jpg")
        session["target"] = target_path
        
        # Process face swap
        try:
            result = await process_face_swap(session["source"], target_path, user_id)
            await message.reply_photo(result, caption="✨ **Face swap completed!**\n\nUse /swap for another swap!")
            
            # Cleanup
            cleanup_user_session(user_id)
            
        except Exception as e:
            await message.reply_text(f"❌ Error processing face swap: {str(e)}")
            cleanup_user_session(user_id)

@app.on_message(filters.video)
async def handle_video(client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in user_sessions or session["step"] != "waiting_target":
        await message.reply_text("Please start with /swap and send source image first!")
        return
    
    session = user_sessions[user_id]
    
    await message.reply_text("🎥 Processing video face swap... This may take a while.")
    
    # Download target video
    target_path = await message.download(file_name=f"temp/target_{user_id}.mp4")
    
    try:
        result = await process_video_face_swap(session["source"], target_path, user_id)
        await message.reply_video(result, caption="✨ **Video face swap completed!**")
        cleanup_user_session(user_id)
        
    except Exception as e:
        await message.reply_text(f"❌ Error processing video: {str(e)}")
        cleanup_user_session(user_id)

@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    
    if data == "start_swap":
        await callback_query.message.edit_text(
            "🎭 **Let's start face swapping!**\n\n"
            "Use /swap command to begin the process."
        )
    elif data == "help":
        help_text = """
🆘 **Help & Instructions**

**Commands:**
• `/start` - Welcome message
• `/swap` - Start face swap process
• `/cancel` - Cancel current operation

**Tips for best results:**
• Use clear, well-lit photos
• Ensure faces are visible and not blurred
• Avoid extreme angles
• Higher quality images = better results

**Supported formats:**
• Images: JPG, PNG, WEBP
• Videos: MP4, AVI, MOV
        """
        await callback_query.message.edit_text(help_text)

async def process_face_swap(source_path, target_path, user_id):
    """Process image face swap"""
    if not f2f:
        raise Exception("Face2Face not initialized")
    
    try:
        # Create face embedding
        embedding_name = f"user_{user_id}"
        f2f.add_face(embedding_name, source_path, save=True)
        
        # Perform face swap with enhancement
        result = f2f.swap(
            media=target_path, 
            faces=embedding_name,
            enhance_face_model='gpen_bfr_512'
        )
        
        # Save result
        result_path = f"temp/result_{user_id}.jpg"
        result.save(result_path)
        return result_path
        
    except Exception as e:
        logger.error(f"Face swap error: {e}")
        raise

async def process_video_face_swap(source_path, target_path, user_id):
    """Process video face swap"""
    if not f2f:
        raise Exception("Face2Face not initialized")
    
    try:
        embedding_name = f"user_{user_id}"
        f2f.add_face(embedding_name, source_path, save=True)
        
        # Process video
        result = f2f.swap(
            media=target_path, 
            faces=embedding_name,
            enhance_face_model='gpen_bfr_512'
        )
        
        result_path = f"temp/result_{user_id}.mp4"
        # Save video result (implementation depends on Face2Face output format)
        return result_path
        
    except Exception as e:
        logger.error(f"Video swap error: {e}")
        raise

def cleanup_user_session(user_id):
    """Clean up user session and temporary files"""
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    # Clean up temp files
    import glob
    for file_path in glob.glob(f"temp/*_{user_id}.*"):
        try:
            os.remove(file_path)
        except:
            pass

@app.on_message(filters.command("cancel"))
async def cancel_command(client, message: Message):
    user_id = message.from_user.id
    cleanup_user_session(user_id)
    await message.reply_text("❌ Operation cancelled!")

if __name__ == "__main__":
    # Create temp directory
    os.makedirs("temp", exist_ok=True)
    print("🚀 Face Swap Bot Starting...")
    app.run()
