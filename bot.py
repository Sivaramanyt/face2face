import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import cv2
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load OpenCV face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

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
• 📸 Simple face swapping
• 🔄 Easy 2-step process
• ⚡ Fast processing

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
• `/status` - Check bot status

**Tips for best results:**
• Use clear, well-lit photos
• Ensure faces are visible and not blurred
• Avoid extreme angles
• Front-facing photos work best

**Supported formats:**
• Images: JPG, PNG, WEBP
        """
        await callback_query.message.edit_text(help_text)
    
    elif data == "about":
        about_text = """
🤖 **About Face Swap Bot**

This bot uses OpenCV technology to swap faces in images.

**Technology:**
• OpenCV face detection
• Python image processing
• Pyrogram Telegram framework

**Version:** 1.0.0
**Platform:** Koyeb deployment

Use responsibly and respect others' privacy!
        """
        await callback_query.message.edit_text(about_text)

async def process_face_swap(source_path, target_path, user_id):
    """Process image face swap using OpenCV"""
    try:
        # Read images
        src_img = cv2.imread(source_path)
        tgt_img = cv2.imread(target_path)
        
        if src_img is None or tgt_img is None:
            raise Exception("Could not read source or target image")
        
        # Convert to grayscale for face detection
        src_gray = cv2.cvtColor(src_img, cv2.COLOR_BGR2GRAY)
        tgt_gray = cv2.cvtColor(tgt_img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        src_faces = face_cascade.detectMultiScale(src_gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        tgt_faces = face_cascade.detectMultiScale(tgt_gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(src_faces) == 0 or len(tgt_faces) == 0:
            raise Exception("No faces detected in source or target image")
        
        # Get the first face from each image
        src_x, src_y, src_w, src_h = src_faces[0]
        tgt_x, tgt_y, tgt_w, tgt_h = tgt_faces[0]
        
        # Extract face regions
        src_face = src_img[src_y:src_y+src_h, src_x:src_x+src_w]
        
        # Resize source face to match target face dimensions
        resized_src_face = cv2.resize(src_face, (tgt_w, tgt_h))
        
        # Create result image
        result_img = tgt_img.copy()
        
        # Replace target face with source face
        result_img[tgt_y:tgt_y+tgt_h, tgt_x:tgt_x+tgt_w] = resized_src_face
        
        # Apply some blending for better results
        mask = np.full((tgt_h, tgt_w, 3), 255, dtype=np.uint8)
        center = (tgt_x + tgt_w//2, tgt_y + tgt_h//2)
        
        # Use seamless cloning for better blending
        try:
            result_img = cv2.seamlessClone(resized_src_face, result_img, mask, center, cv2.NORMAL_CLONE)
        except:
            # If seamless cloning fails, use simple replacement
            pass
        
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

🤖 Face Detection: ✅ OpenCV Ready
📁 Active Sessions: {len(user_sessions)}
💾 Memory: Ready
🔄 Status: Online
⚡ Processing: Fast & Simple

Ready to swap faces! 🎭
    """
    await message.reply_text(status_text)

if __name__ == "__main__":
    # Create temp directory
    os.makedirs("temp", exist_ok=True)
    print("🚀 Face Swap Bot Starting...")
    print("✅ Using OpenCV for face processing")
    bot_app.run()
    
