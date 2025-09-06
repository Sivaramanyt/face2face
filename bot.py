import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import cv2
import numpy as np
from flask import Flask, jsonify
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for health check
flask_app = Flask(__name__)

@flask_app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "bot": "face_swap_bot"}), 200

@flask_app.route('/')
def home():
    return jsonify({"message": "Face Swap Bot is running!", "status": "active"}), 200

# Load OpenCV face detector and predictor for better results
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
🎭 **Professional Face Swap Bot** 🎭

Welcome! I can swap faces in images with realistic results.

**Features:**
• 📸 Advanced face swapping
• 🔄 Easy 2-step process
• ✨ Natural blending
• ⚡ Fast processing

**How to use:**
1. Send /swap to start
2. Upload source image (your face)
3. Upload target image
4. Get your professional result!

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
        "📸 Upload a clear, front-facing photo with good lighting"
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
        await message.reply_text("🔄 Processing your professional face swap...")
        
        # Download target image
        target_path = await message.download(file_name=f"temp/target_{user_id}.jpg")
        session["target"] = target_path
        
        # Process face swap
        try:
            result_path = await process_advanced_face_swap(session["source"], target_path, user_id)
            await message.reply_photo(result_path, caption="✨ **Professional face swap completed!**\n\nUse /swap for another swap!")
            
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
            "🎭 **Let's create a professional face swap!**\n\n"
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
• Front-facing poses work best
• Avoid sunglasses or masks
• High resolution images preferred
• Similar face angles give better results

**Supported formats:**
• Images: JPG, PNG, WEBP
        """
        await callback_query.message.edit_text(help_text)
    
    elif data == "about":
        about_text = """
🤖 **About Professional Face Swap Bot**

This bot uses advanced OpenCV techniques for realistic face swapping.

**Technology:**
• OpenCV face detection
• Advanced blending algorithms
• Color matching
• Seamless cloning

**Version:** 2.0.0
**Platform:** Koyeb deployment

Use responsibly and respect others' privacy!
        """
        await callback_query.message.edit_text(about_text)

async def process_advanced_face_swap(source_path, target_path, user_id):
    """Process advanced face swap with better blending"""
    try:
        # Read images
        src_img = cv2.imread(source_path)
        tgt_img = cv2.imread(target_path)
        
        if src_img is None or tgt_img is None:
            raise Exception("Could not read source or target image")
        
        # Convert to grayscale for face detection
        src_gray = cv2.cvtColor(src_img, cv2.COLOR_BGR2GRAY)
        tgt_gray = cv2.cvtColor(tgt_img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces with better parameters
        src_faces = face_cascade.detectMultiScale(src_gray, scaleFactor=1.05, minNeighbors=8, minSize=(50, 50))
        tgt_faces = face_cascade.detectMultiScale(tgt_gray, scaleFactor=1.05, minNeighbors=8, minSize=(50, 50))
        
        if len(src_faces) == 0 or len(tgt_faces) == 0:
            raise Exception("No faces detected in source or target image")
        
        # Get the largest faces (most prominent)
        src_face = max(src_faces, key=lambda x: x[2] * x[3])  # largest by area
        tgt_face = max(tgt_faces, key=lambda x: x[2] * x[3])
        
        src_x, src_y, src_w, src_h = src_face
        tgt_x, tgt_y, tgt_w, tgt_h = tgt_face
        
        # Extract face regions with some padding
        padding = 10
        src_face_region = src_img[max(0, src_y-padding):src_y+src_h+padding, 
                                 max(0, src_x-padding):src_x+src_w+padding]
        
        # Resize source face to match target face dimensions
        resized_src_face = cv2.resize(src_face_region, (tgt_w + 2*padding, tgt_h + 2*padding))
        
        # Create result image
        result_img = tgt_img.copy()
        
        # Create an elliptical mask for more natural blending
        mask = np.zeros((tgt_h + 2*padding, tgt_w + 2*padding, 3), dtype=np.uint8)
        center = (mask.shape[1]//2, mask.shape[0]//2)
        axes = (tgt_w//2, tgt_h//2)
        cv2.ellipse(mask, center, axes, 0, 0, 360, (255, 255, 255), -1)
        
        # Apply Gaussian blur to mask for smoother blending
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        
        # Adjust target position for padding
        adj_x = max(0, tgt_x - padding)
        adj_y = max(0, tgt_y - padding)
        adj_w = min(tgt_img.shape[1] - adj_x, tgt_w + 2*padding)
        adj_h = min(tgt_img.shape[0] - adj_y, tgt_h + 2*padding)
        
        # Resize mask and face to fit adjusted dimensions
        if adj_w != tgt_w + 2*padding or adj_h != tgt_h + 2*padding:
            resized_src_face = cv2.resize(resized_src_face, (adj_w, adj_h))
            mask = cv2.resize(mask, (adj_w, adj_h))
        
        # Color correction - match the average color of target face region
        tgt_face_region = result_img[adj_y:adj_y+adj_h, adj_x:adj_x+adj_w]
        if tgt_face_region.size > 0:
            tgt_mean = np.mean(tgt_face_region, axis=(0, 1))
            src_mean = np.mean(resized_src_face, axis=(0, 1))
            
            # Adjust source face color to match target
            for i in range(3):
                if src_mean[i] > 0:
                    resized_src_face[:, :, i] = np.clip(
                        resized_src_face[:, :, i] * (tgt_mean[i] / src_mean[i]), 0, 255
                    )
        
        # Apply advanced blending
        mask_norm = mask.astype(float) / 255.0
        
        # Blend the images
        for i in range(3):
            result_img[adj_y:adj_y+adj_h, adj_x:adj_x+adj_w, i] = (
                mask_norm[:, :, i] * resized_src_face[:, :, i] +
                (1 - mask_norm[:, :, i]) * result_img[adj_y:adj_y+adj_h, adj_x:adj_x+adj_w, i]
            )
        
        # Apply additional smoothing at edges
        center_point = (adj_x + adj_w//2, adj_y + adj_h//2)
        
        # Try seamless cloning for even better results
        try:
            final_mask = np.zeros((adj_h, adj_w), dtype=np.uint8)
            cv2.ellipse(final_mask, (adj_w//2, adj_h//2), (adj_w//3, adj_h//3), 0, 0, 360, 255, -1)
            result_img = cv2.seamlessClone(
                resized_src_face.astype(np.uint8), 
                result_img.astype(np.uint8), 
                final_mask, 
                center_point, 
                cv2.NORMAL_CLONE
            )
        except Exception as e:
            logger.warning(f"Seamless cloning failed: {e}, using blended result")
        
        # Final touch: slight Gaussian blur on the blended edges
        result_img = cv2.GaussianBlur(result_img, (3, 3), 0)
        
        # Save result
        result_path = f"temp/result_{user_id}.jpg"
        cv2.imwrite(result_path, result_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        return result_path
        
    except Exception as e:
        logger.error(f"Advanced face swap processing error: {e}")
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

🤖 Face Detection: ✅ Advanced OpenCV Ready
📁 Active Sessions: {len(user_sessions)}
💾 Memory: Optimized
🔄 Status: Online
⚡ Processing: Professional Quality
🎭 Blending: Advanced Algorithms

Ready to create amazing face swaps! ✨
    """
    await message.reply_text(status_text)

def run_flask():
    """Run Flask server for health checks"""
    flask_app.run(host="0.0.0.0", port=8080, debug=False)

if __name__ == "__main__":
    # Create temp directory
    os.makedirs("temp", exist_ok=True)
    
    # Start Flask server in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    print("🚀 Face Swap Bot Starting...")
    print("✅ Using Advanced OpenCV face processing")
    print("🌐 Health check server running on port 8080")
    
    # Start the bot
    bot_app.run()
