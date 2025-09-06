import os
import tempfile
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from insightface.app import FaceAnalysis
import cv2
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize face analysis
try:
    app_face = FaceAnalysis(name='buffalo_l')
    app_face.prepare(ctx_id=-1, det_size=(640, 640))  # CPU mode ctx_id=-1
    logger.info("Face analysis initialized successfully")
except Exception as e:
    logger.error(f"Face analysis initialization failed: {e}")
    app_face = None

# Bot setup with your credentials
bot_app = Client(
    "face_swap_bot",
    bot_token="8261755198:AAFikWiiAzIuRN_p8UmAtWslhhy18ia2TBg",
    api_id=29542645,
    api_hash="06e505b8418565356ae79365df5d69e0"
)

# User sessions to track face swap process
user_sessions = {}

@bot_app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    welcome_text = """
🎭 **Face Swap Bot** 🎭

Welcome! I can swap faces in images.

**Features:**
• 📸 Image face swapping
• 🔄 Easy 2-step process
• ✨ High quality results

**How to use:**
1. Send /swap to start
2. Upload source image (your face)
3. Upload target image
4. Get your swapped result!

Choose an option below:
    """
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Start Face Swap", callback_data="start_swap")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        [InlineKeyboardButton("⚙️ About", callback_data="about")]
    ])
    
    await message.reply_text(welcome_text, reply_markup=keyboard)

@bot_app.on_message(filters.command("swap"))
async def swap_command(client, message: Message):
    user_id = message.from_user.id
    user_sessions[user_id] = {"step": "waiting_source", "source": None, "target": None}
    
    await message.reply_text(
        "🎭 **Face Swap Process Started!**\n\n"
        "**Step 1:** Send me the source image (the face you want to use)\n"
        "📸 Upload a clear photo with a visible face"
    )

@bot_app.on_message(filters.photo)
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
            "**Step 2:** Now send me the target image\n"
            "🎯 This is where the face will be swapped"
        )
    
    elif session["step"] == "waiting_target":
        await message.reply_text("🔄 Processing your face swap...")
        
        # Download target image
        target_path = await message.download(file_name=f"temp/target_{user_id}.jpg")
        session["target"] = target_path
        
        # Process face swap
        try:
            result_path = await process_face_swap(session["source"], target_path, user_id)
            await message.reply_photo(result_path, caption="✨ **Face swap completed!**\n\nUse /swap for another swap!")
            
            # Cleanup
            cleanup_user_session(user_id)
            
        except Exception as e:
            await message.reply_text(f"❌ Error processing face swap: {str(e)}")
            cleanup_user_session(user_id)

@bot_app.on_callback_query()
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
        """
        await callback_query.message.edit_text(help_text)
    
    elif data == "about":
        about_text = """
🤖 **About Face Swap Bot**

This bot uses advanced AI technology to swap faces in images.

**Technology:**
• InsightFace AI models
• OpenCV image processing
• Pyrogram Telegram framework

**Developer:** @YourUsername
**Version:** 1.0.0

Use responsibly and respect others' privacy!
        """
        await callback_query.message.edit_text(about_text)

async def process_face_swap(source_path, target_path, user_id):
    """Process image face swap using InsightFace"""
    if not app_face:
        raise Exception("Face analysis not initialized")
    
    try:
        # Read images
        src_img = cv2.imread(source_path)
        tgt_img = cv2.imread(target_path)
        
        if src_img is None or tgt_img is None:
            raise Exception("Could not read source or target image")
        
        # Detect faces
        src_faces = app_face.get(src_img)
        tgt_faces = app_face.get(tgt_img)
        
        if not src_faces or not tgt_faces:
            raise Exception("No faces detected in source or target image")
        
        # Get the first face from each image
        src_face = src_faces[0]
        tgt_face = tgt_faces[0]
        
        # Extract face regions with proper boundary checking
        src_bbox = src_face.bbox.astype(int)
        tgt_bbox = tgt_face.bbox.astype(int)
        
        # Ensure boundaries are within image dimensions
        src_y1, src_y2 = max(0, src_bbox[1]), min(src_img.shape[0], src_bbox[3])
        src_x1, src_x2 = max(0, src_bbox[0]), min(src_img.shape[1], src_bbox[2])
        
        tgt_y1, tgt_y2 = max(0, tgt_bbox[1]), min(tgt_img.shape[0], tgt_bbox[3])
        tgt_x1, tgt_x2 = max(0, tgt_bbox[0]), min(tgt_img.shape[1], tgt_bbox[2])
        
        # Extract source face
        src_face_region = src_img[src_y1:src_y2, src_x1:src_x2]
        
        if src_face_region.size == 0:
            raise Exception("Could not extract source face region")
        
        # Resize source face to match target face dimensions
        target_height = tgt_y2 - tgt_y1
        target_width = tgt_x2 - tgt_x1
        
        if target_height <= 0 or target_width <= 0:
            raise Exception("Invalid target face dimensions")
        
        resized_src_face = cv2.resize(src_face_region, (target_width, target_height))
        
        # Simple face swap: replace target face with source face
        result_img = tgt_img.copy()
        result_img[tgt_y1:tgt_y2, tgt_x1:tgt_x2] = resized_src_face
        
        # Save result
        result_path = f"temp/result_{user_id}.jpg"
        cv2.imwrite(result_path, result_img)
        
        return result_path
        
    except Exception as e:
        logger.error(f"Face swap processing error: {e}")
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

@bot_app.on_message(filters.command("cancel"))
async def cancel_command(client, message: Message):
    user_id = message.from_user.id
    cleanup_user_session(user_id)
    await message.reply_text("❌ Operation cancelled!")

@bot_app.on_message(filters.command("status"))
async def status_command(client, message: Message):
    status_text = f"""
📊 **Bot Status**

🤖 Face Analysis: {'✅ Ready' if app_face else '❌ Not initialized'}
📁 Active Sessions: {len(user_sessions)}
💾 Memory: Ready
🔄 Status: Online

Ready to swap faces! 🎭
    """
    await message.reply_text(status_text)

if __name__ == "__main__":
    # Create temp directory
    os.makedirs("temp", exist_ok=True)
    print("🚀 Face Swap Bot Starting...")
    print("✅ Using InsightFace for face processing")
    bot_app.run()
    
